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


class TriggerHunterThread(QtCore.QThread):
    def __init__(self, outputs, host, port, parent=None):
        QtCore.QThread.__init__(self)
        self.outputs = outputs

        self.addr = "tcp://{}:{}".format(host, port)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.socket.bind(self.addr)
        
        self.lock = Mutex()
        self.running = True

        self.current_pos = 0
            
    def run(self):
        # dump message in the queue
        while True:
            try:
                msg = self.socket.recv(zmq.NOBLOCK)
            except zmq.ZMQError:
                break

        while self.running:
            # Wait for next triggers from client
            msg = self.socket.recv()
            
            # TODO locate and abort the b'21' push in the game
            if (msg != b'21'):
                trig = msg.decode().split("/")
                eventTime = (float)(trig[0])
                label = (int)(trig[1])

                # filter only triggers needed
                if ( 1 <= label <= 9 ):
                    # check latency
                    posixtime = time.time() * 1000
                    latency = posixtime - eventTime
                    # print( "time : {}, label : {} -> latency({}ms)".format(eventTime, label, int(latency)))

                    nb_marker = 1
                    markers = np.empty((nb_marker,), dtype=_dtype_trigger)
                    markers['pos'][0] = self.current_pos
                    markers['points'][0] = 0
                    markers['channel'][0] = 0
                    markers['type'][0] = b'Stimulus'
                    markers['description'][0] = "S  {}".format(label).encode("utf-8")
                    # print(markers)
                    self.outputs['triggers'].send(markers, index=nb_marker)
            elif (msg is b'stop'):
                self.running = False

    def stop(self):
        with self.lock:
            self.running = False

            self.socket.disconnect(self.addr)

class TriggerHunter(Node):

    _input_specs = {'signals': dict(streamtype='signals')}
    
    _output_specs = {'triggers': dict(streamtype = 'event', dtype = _dtype_trigger,
                                                shape = (-1,)),
                                }
    
    def __init__(self, **kargs):
        Node.__init__(self, **kargs)

    def _configure(self, host="127.0.0.1", port=5556):
        self.host = host
        self.port = port

    def _initialize(self):
        self._thread = TriggerHunterThread(self.outputs, self.host, self.port, parent=self)

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
        self._thread.current_pos = ptr

