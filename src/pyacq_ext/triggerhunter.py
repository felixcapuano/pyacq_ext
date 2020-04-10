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

    QUIT_ZMQ = "0"
    START_ZMQ = "1"
    EVENT_ZMQ = "2"
    RESULT_ZMQ = "4"
    OK_ZMQ = "5"

    def __init__(self, outputs, host, port, parent=None):
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

        self.request, self.content = None, None
        self.current_pos = 0
        self.reset()
        

    def run(self):
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
                    print("disconnected")

                elif (self.request == self.START_ZMQ):
                    self.socket.send_string(self.START_ZMQ)
                    self.isConnected = True
                    print("connect with : ", self.addr)

                elif (self.request == self.EVENT_ZMQ and self.isConnected):
                    self.socket.send_string(self.OK_ZMQ)
                    self.new_event()

                elif (self.request == self.RESULT_ZMQ and self.isConnected):
                    self.wait_result()
                    if not (self.result_frame == None):
                        print("result : ", self.result_frame)
                        self.socket.send_string(self.result_frame)
                    else:
                        print("No Result")
                        self.socket.send_string(self.QUIT_ZMQ)
                    self.reset()

            except zmq.ZMQError:
                pass
            

    
    def new_event(self):
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

    def wait_result(self):
        # TODO ???? NOT SURE IT WORKING
        
        repeat = 10
        counter = 0
        shift = 100
        while(self.result_frame == None and counter < 10):
            print("sleep {}ms until new result check \
                    ({}/{})".format(shift,counter+1,repeat))
            self.msleep(shift)
            counter += 1

    
    def set_current_pos(self, ptr):
        with self.mutex:
            self.current_pos = ptr

    def set_result_frame(self, frame):
        with self.mutex:
            self.result_frame = frame
    
    def get_request(self):
        with self.mutex:
            return self.request, self.content

    def reset(self):
        self.result_frame = None

    def stop(self):
        with self.mutex:
            self.running = False
            self.socket.disconnect(self.addr)

class EventPoller(Node):

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
        self._thread = EventPollerThread(self.outputs, self.host, self.port, parent=self)

        self._poller = ThreadPollInput(self.inputs['signals'], return_data=True)
        self._poller.new_data.connect(self.on_new_chunk)

    def _start(self):
        self._poller.start()
        self._thread.start()

    def _stop(self):
        self._thread.stop()
        self._thread.wait()

        self._poller.stop()
        self._poller.wait()

    def _close(self):
        pass

    def on_new_chunk(self, ptr, data):
        self._thread.set_current_pos(ptr)

    def send_result(self, frame):
        self._thread.set_result_frame(frame)
    
    def get_current_request(self):
        return self._thread.get_request()

    def reset(self):
        self._thread.reset()
