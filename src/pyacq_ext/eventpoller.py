import time

import numpy as np
import zmq
from PyQt5 import QtCore
from pyqtgraph.util.mutex import Mutex

from pyacq.core import Node, ThreadPollInput

from datetime import datetime

from .helper import Helper

_dtype_trigger = [('pos', 'int64'),
                ('points', 'int64'),
                ('channel', 'int64'),
                ('type', 'S16'),  # TODO check size
                ('description', 'S100'),  # TODO check size
                  ('additionalInformation', 'S100'),
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

    START_CALIBRATION_ZMQ = "6"
    RESET_ZMQ = "7"
    CALIBRATION_CHECK = "8"
    TRIGGERSETUP_ZMQ = "9"



    stop_communicate = QtCore.pyqtSignal()

    def __init__(self, outputs, host, port, helper, parent=None):
        """Initialize the socket"""
        QtCore.QThread.__init__(self)
        self.outputs = outputs
        self.addr = "tcp://{}:{}".format(host, port)

        self.context = zmq.Context()
        #self.socket = self.context.socket(zmq.REP)
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(self.addr)
        
        self.mutex = Mutex()

        # thread and zmq state
        self.running = False 
        self.isConnected = False
        self.result_frame = None

        self.current_pos = 0
        self.reset()
        
        self.posXTime0 = 0
        self.samplingRate = 0

        #now = datetime.now()
        #dt_string = now.strftime("%Y.%m.%d-%H.%M.%S")
        #filename  = "C:/Users/AlexM/Documents/Projets/Python/pybart/log/Trig-" +  dt_string + ".txt"
        #self.TrigFile = open(filename, "a+")

        self.calibrationMode = False
        self.helper = helper

        self.pingSent = False


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
                if self.pingSent is False:
                    self.pingSent = True
                    self.socket.send_string(self.OK_ZMQ + "|")  # Ping sent to let Unity know that framework is started


                msg = self.socket.recv(zmq.NOBLOCK)
                
                self.request, self.content = msg.decode().split("|")
                if (self.request == self.QUIT_ZMQ):
                    response = self.request + "|" + self.content
                    self.socket.send_string(response)
                    self.isConnected = False
                    self.reset()
                    print("Stop acquiring")

                elif (self.request == self.START_ZMQ):
                    response = self.request + "|" + self.content
                    self.socket.send_string(response)
                    self.isConnected = True
                    print("Acquiring on : ", self.addr)

                elif (self.request == self.EVENT_ZMQ and self.isConnected):
                    response = self.request + "|" + self.content
                    self.socket.send_string(response)
                    self.new_event()

                elif (self.request == self.RESULT_ZMQ and self.isConnected):
                    self.helper.resultSignal.emit()
                    #self.wait_result()
                    #if not (self.result_frame == None):
                        #print("Sending result")
                        #self.socket.send_string(self.result_frame)
                    #else:
                        #print("No Result")
                        #self.socket.send_string(self.QUIT_ZMQ)
                    #self.reset()

                elif (self.request == self.START_CALIBRATION_ZMQ and self.isConnected):
                    response = self.request + "|" + self.content
                    self.socket.send_string(response)
                    self.helper.resetSignal.emit(True)

                elif(self.request == self.RESET_ZMQ and self.isConnected):
                    response = self.request + "|" + self.content
                    self.socket.send_string(response)
                    self.helper.resetSignal.emit(False)

                elif(self.request == self.CALIBRATION_CHECK and self.isConnected):
                    if(not self.calibrationMode):
                        response = self.request + "|" + self.content
                        self.socket.send_string(response)
                    else:
                        self.socket.send_string("-1") # TODO : ce message déconnectera unity et python, ce qui n'est pas forcément ce qu'on veut, faire en sorte qu'il indique seulement un fail de calibration

                elif(self.request == self.TRIGGERSETUP_ZMQ and self.isConnected):
                    response = self.request + "|" + self.content
                    self.socket.send_string(response)
                    self.helper.triggerSetupSignal.emit(self.content)

            except zmq.ZMQError:
                pass
            


    def new_event(self):
        """Call when event is sended by the game"""
        # check latency
        msg_data = self.content.split("/")

        eventTime = (float)(msg_data[0].replace(',','.'))

        msg_dataTab = msg_data[1].split(';')
        label = msg_dataTab[0]
        additionalInformation = ""
        for i in range(1, len(msg_dataTab)):
            additionalInformation += msg_dataTab[i]

        posixtime = time.time() * 1000
        latency = posixtime - eventTime
        #print("EventTime : ", eventTime )
        #print("EventId : ", eventId )

        # print( "time : {}, eventId : {} -> latency({}ms)".format(eventTime,
        #     eventId, int(latency)))
    
        nb_marker = 1
        markers = np.empty((nb_marker,), dtype=_dtype_trigger)
        #markers['pos'][0] = self.current_pos
        print("posXTime0 : ", self.posXTime0 )
        pos_curr= round(((eventTime-self.posXTime0)*1000)/self.samplingRate)
        
        
        #self.TrigFile.write(str(pos_curr)  + '\n')
        
        markers['pos'][0] = pos_curr
        markers['points'][0] = 0
        markers['channel'][0] = 0
        markers['type'][0] = b'Stimulus'
        markers['description'][0] = "{}".format(label).encode("utf-8")
        markers['additionalInformation'][0] = "{}".format(additionalInformation).encode("utf-8")

        #print(markers, "latency : ", latency)

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
            if not (self.result_frame == None):
                print("Sending result")
                self.socket.send_string(self.result_frame)
            else:
                print("No Result")
                self.socket.send_string(self.QUIT_ZMQ)
            self.reset()
    
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
            #self.TrigFile.close()
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
        self.helper = Helper()
        self.sender_poller = EventPollerThread(self.outputs, self.host, self.port, self.helper, parent=self)

        self._poller = ThreadPollInput(self.inputs['signals'], return_data=True)
        self._poller.new_data.connect(self.on_new_chunk)
        #now = datetime.now()
        # dd/mm/YY H:M:S
        #dt_string = now.strftime("%Y.%m.%d-%H.%M.%S")
        #filename  = "C:/Users/AlexM/Documents/Projets/Python/pybart/log/Data-" +  dt_string + ".txt"
        #filenamePosXData  = "C:/Users/AlexM/Documents/Projets/Python/pybart/log/PosXData-" +  dt_string + ".txt"
        #self.dataFile = open(filename, "a+")
        #self.posXDataFile = open(filenamePosXData, "a+")
        self.sender_poller.samplingRate = self._poller.input_stream().params['sample_rate']

    def _start(self):
        self._poller.start()
        self.sender_poller.start()

    def _stop(self):
        self.sender_poller.stop()
        self.sender_poller.wait()

        self._poller.stop()
        self._poller.wait()
        #self.dataFile.close()
        #self.posXDataFile.close()
    def _close(self):
        pass

    def on_new_chunk(self, ptr, data):
        self.sender_poller.set_current_pos(ptr)
        if (ptr==data.shape[0]):
            
            self.ArrayPtr = []
            self.ArrayPtr.append(ptr)
            self.ArrayposiXTime = []
            self.ArrayposiXTime.append(0)
            self.PosiXTime1stChunk =time.time() * 1000
            
            chunkDuration = data.shape[0] * 1000 /  self.sender_poller.samplingRate 
            #print("chunkDuration : \n", chunkDuration)
            #print("ptr : \n", ptr)
            
            self.sender_poller.posXTime0 = (time.time() * 1000) - chunkDuration
            #print("posXTime0 : \n", self.sender_poller.posXTime0 )
            
        if ((ptr>data.shape[0]) and (ptr<(60000* 1000 /  self.sender_poller.samplingRate ))  ):
            self.ArrayPtr.append(ptr)
            self.ArrayposiXTime.append((time.time() * 1000) - self.PosiXTime1stChunk)
             
            if ((ptr%(200 * 1000 /  self.sender_poller.samplingRate )) ==0 ):
                p = np.polyfit(np.array( self.ArrayposiXTime ), np.array(self.ArrayPtr),1)
                #print("Delay 1st chunk: \n ",p[1])
                self.sender_poller.posXTime0 =self.PosiXTime1stChunk - p[1]
                #print("posXTime0 : \n ", self.sender_poller.posXTime0)
                
                
        
            
            
        #datamatrix = np.matrix(data)
        #for line in datamatrix:
            #np.savetxt(self.dataFile, line, fmt='%f')
        
        #print("ptr : \n", ptr)
        #print("time : \n", str(time.time() * 1000))
        #self.posXDataFile.write(str(time.time() * 1000)  + '\n')

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
