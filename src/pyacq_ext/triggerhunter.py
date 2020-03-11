import time

import zmq
from PyQt5 import QtCore
from pyqtgraph.util.mutex import Mutex

from pyacq.core import Node
from src.pyacq_ext.brainvisionlistener import BrainVisionListener

_dtype_trigger = [('pos', 'int64'),
                ('points', 'int64'),
                ('channel', 'int64'),
                ('type', 'S16'),  # TODO check size
                ('description', 'S16'),  # TODO check size
                ]


class TriggerHunterThread(QtCore.QThread):
    def __init__(self, host, port, parent=None):
        QtCore.QThread.__init__(self)

        context = zmq.Context()
        self.socket = context.socket(zmq.PULL)
        self.socket.bind("tcp://{}:{}".format(host, port))
        
        self.lock = Mutex()
        self.running = True
            
    def run(self):
        while True:
            with self.lock:
                    if not self.running:
                        break

            # Wait for next triggers from client
            
            triggers = self.socket.recv()
            
            if (triggers != b'21'):
                trig = triggers.decode().split("/")
                eventTime = (float)(trig[0])
                label = (int)(trig[1])

                # filter only triggers needed
                if ( 1 <= label <= 9 ):
                    # check latency
                    posixtime = time.time() * 1000
                    latency = posixtime - eventTime
                    print( "time : {}, label : {} -> latency({}ms)".format(eventTime, label, int(latency)))



    def stop(self):
        with self.lock:
            self.running = False

class TriggerHunter(Node):
    
    _output_specs = {'triggers': dict(streamtype = 'event', dtype = _dtype_trigger,
                                                shape = (-1,)),
                                }
    
    def __init__(self, **kargs):
        Node.__init__(self, **kargs)

    def _configure(self, bvlistener, host="127.0.0.1", port=5556):
        self.host = host
        self.port = port

        if not isinstance(bvlistener, BrainVisionListener):
            raise ValueError("bvlistener is {} type while BrainVisionListener type expected.".format(type(bvlistener)))

        self.bvlistener = bvlistener

    def _initialize(self):
        self._thread = TriggerHunterThread(self.host, self.port, parent=self)
        self.bvlistener._thread.sig_new_chunk

    def _start(self):
        self._thread.start()

    def _stop(self):
        self._thread.stop()
        self._thread.wait()

    def _close(self):
        pass
