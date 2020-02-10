import numpy as np
import pyqtgraph as pg
from pyacq.core import WidgetNode, register_node_type
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QPushButton
from pyqtgraph.Qt import QtCore, QtGui
import time
import random

_dtype_trigger = [('pos', 'int64'),
            ('points', 'int64'),
            ('channel', 'int64'),
            ('type', 'S16'),  # TODO check size
            ('description', 'S16'),  # TODO check size
            ]

class TriggerEmulator(WidgetNode):



    _output_specs = {'triggers': dict(streamtype='event', dtype=_dtype_trigger,
                                      shape=(-1,)),
                     }

    def __init__(self, **kargs):
        WidgetNode.__init__(self, **kargs)

        self.title = 'Trigger Emulator'
        self.left = 100
        self.top = 100
        self.width = 320
        self.height = 200
        self.initUI()

        self.start_time = int(time.time()*1000)
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        button = QPushButton('Send trigger', self)
        button.move(0,0)
        button.resize(self.width,self.height)
        button.clicked.connect(self.on_click)
        

    @pyqtSlot()
    def on_click(self):
        
        nb_marker = 1

        trig = np.empty((nb_marker,), dtype=_dtype_trigger)
        
        trig['pos'] = int(time.time()*1000)-self.start_time
        trig['points'] = 0
        trig['channel'] = -1
        trig['type'] = b'Stimulus'

        # description = [b'S  1', b'S  2', b'S  3', b'S  4', b'S  5', b'S  6', b'S  7']
        # trig['description'] = random.choice(description) 
        trig['description'] = b'S  1'

        print('Trigger lauch : {}'.format(trig))
        
        self.outputs['triggers'].send(trig, index=nb_marker)

    def _configure(self, **kargs):
        pass
    
    def _initialize(self):
        pass

    def _start(self):
        pass

    def _stop(self):
        pass
    
    def _close(self):
        pass


if __name__ == '__main__':
    app = QtGui.QApplication([])

    te = TriggerEmulator()
    te.configure()
    te.outputs['triggers'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    te.initialize()
    te.show()

    te.start()

    app.exec_()
