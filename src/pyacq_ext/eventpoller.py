import time

import numpy as np
import zmq
from PyQt5 import QtCore
from pyqtgraph.util.mutex import Mutex

from pyacq.core import Node, ThreadPollInput

_dtype_trigger = [('pos', 'int64'),
                ('points', 'int64'),
                ('channel', 'int64'),
                ('type', 'S16'),  # TODO check size
                ('description', 'S16'),  # TODO check size
                ]


class EventPollerThread(QtCore.QThread):
    """Communicate with the MYB via ZeroMQ.

    This is a thread of communication beetween the myb game and pyacq.
    The communication architecture is request-response.
    
    """
    QUIT_ZMQ = "0"
    START_ZMQ = "1"
    EVENT_ZMQ = "2"
    RESULT_ZMQ = "4"
    OK_ZMQ = "5"

    stop_communicate = QtCore.pyqtSignal()

    def __init__(self, outputs, host, port, parent=None):
        """Initialize the socket"""
        QtCore.QThread.__init__(self)
        self.outputs = outputs

        self.addr = "tcp://{}:{}".format(host, port)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self.addr)
        
        self.mutex = Mutex()

        # thread and zmq state
        self.running = False 
        self.isConnected = False
        self.result_frame = None

        self.current_pos = 0
        self.reset()
        

    def run(self):
        """The thread core wait request from the game and send back response

        The frame patern is : <request_type>|<content>

        There is 5 types of <request_type> :

        - **QUIT (value = 0)** received when communication has to stop
        - **START (value = 1)** received when communication is ready to start
        - **EVENT (value = 2)** just received a new event, content is type
          <event_time>/<event_id>
        - **RESULT (value = 4)** received when myb game is ready to receive
          a result, content is type : <nb_total_event>
        - **OK (value = 5)** receive when all is fine

        Communication sample :

        | [MYB] START
        | [PYACQ] OK
        | [MYB] EVENT
        | [PYACQ] OK
        | [MYB] EVENT
        | [PYACQ] OK
        |     ....
        | [MYB] RESULT
        | [PYACQ] "__/__ .... __/__" (result frame)

        """
        self.running = True
        while True:
            with self.mutex:
                if not self.running:
                    break

            try:
                msg = self.socket.recv(zmq.NOBLOCK)
                
                self.request, self.content = msg.decode().split("|")
                
                if (self.request == self.QUIT_ZMQ):
                    self.socket.send_string(self.OK_ZMQ)
                    self.isConnected = False
                    self.reset()
                    print("Stop acquiring")

                elif (self.request == self.START_ZMQ):
                    self.socket.send_string(self.START_ZMQ)
                    self.isConnected = True
                    print("Acquiring on : ", self.addr)

                elif (self.request == self.EVENT_ZMQ and self.isConnected):
                    self.socket.send_string(self.OK_ZMQ)
                    self.new_event()

                elif (self.request == self.RESULT_ZMQ and self.isConnected):
                    self.wait_result()
                    if not (self.result_frame == None):
                        print("Sending result")
                        self.socket.send_string(self.result_frame)
                    else:
                        print("No Result")
                        self.socket.send_string(self.QUIT_ZMQ)
                    self.reset()

            except zmq.ZMQError:
                pass
            

    
    def new_event(self):
        """Call when event is sended by the game"""
        # check latency
        msg_data = self.content.split("/")

        eventTime = (float)(msg_data[0].replace(',','.'))
        eventId = (int)(msg_data[1])

        posixtime = time.time() * 1000
        latency = posixtime - eventTime
        # print( "time : {}, eventId : {} -> latency({}ms)".format(eventTime,
        #     eventId, int(latency)))
    
        nb_marker = 1
        markers = np.empty((nb_marker,), dtype=_dtype_trigger)
        markers['pos'][0] = self.current_pos
        markers['points'][0] = 0
        markers['channel'][0] = 0
        markers['type'][0] = b'Stimulus'
        markers['description'][0] = "S  {}".format(eventId).encode("utf-8")
        print(markers, "latency : ", latency)

        self.outputs['triggers'].send(markers, index=nb_marker)

    def wait_result(self, repeat=10, counter=0, shift=100):
        """Call when result is waited by the game

        This function pause the thread when the result is processed.
        and check if no result has ready to send during a period of time.
        """
        
        while(self.result_frame == None and counter < 10):
            print("sleep {}ms until new result check" \
                    "({}/{})".format(shift,counter+1,repeat))
            self.msleep(shift)
            counter += 1

    
    def set_current_pos(self, ptr):
        """Use to syncronise the EEG stream with game event"""
        with self.mutex:
            self.current_pos = ptr

    def set_result_frame(self, frame):
        """Use to set the result when it's ready to send"""
        with self.mutex:
            self.result_frame = frame
    
    def get_request(self):
        """Get the current request sender by the game"""
        with self.mutex:
            return self.request, self.content

    def reset(self):
        """Use to reset the result frame"""
        self.result_frame = None

    def stop(self):
        """Stop the thread"""
        with self.mutex:
            self.running = False
            self.socket.disconnect(self.addr)

class EventPoller(Node):
    """This node is use to communicate with MYB games

    This node have 1 signal input and 1 triggers output.
    The node detect events from the MYB game using socket (zeromq)
    and convert them to pyacq event stream.
    The node have two poller: the first wait a signal and the second listen
    a tcp address to etablish communication with MYB game.
    
    """
    _input_specs = {'signals': dict(streamtype='signals')}
    
    _output_specs = {'triggers': dict(streamtype = 'event', dtype = _dtype_trigger,
                                                shape = (-1,)),
                                }
    
    def __init__(self, **kargs):
        Node.__init__(self, **kargs)
        

    def _configure(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port

    def _initialize(self):
        self.sender_poller = EventPollerThread(self.outputs, self.host, self.port, parent=self)

        self._poller = ThreadPollInput(self.inputs['signals'], return_data=True)
        self._poller.new_data.connect(self.on_new_chunk)

    def _start(self):
        self._poller.start()
        self.sender_poller.start()

    def _stop(self):
        self.sender_poller.stop()
        self.sender_poller.wait()

        self._poller.stop()
        self._poller.wait()

    def _close(self):
        pass

    def on_new_chunk(self, ptr, data):
        self.sender_poller.set_current_pos(ptr)

    def send_result(self, frame):
        """Set the formatted result ready to send

        You can set the result to send with this method.
        If the game is asking a result the node will send this 
        result then this result will be reset.
        """
        self.sender_poller.set_result_frame(frame)
    
    def get_current_request(self):
        """Get the current request send by the MYB game"""
        return self.sender_poller.get_request()

    def reset(self):
        self.sender_poller.reset()
