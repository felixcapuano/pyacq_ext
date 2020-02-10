# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.


import pytest
import scipy.signal
from pyqtgraph.Qt import QtCore, QtGui

import pyacq
from pyacq import create_manager
from pyacq.devices.brainampsocket import BrainAmpSocket
from pyacq.dsp.sosfilter import SosFilter
from pyacq.viewers.qoscilloscope import QOscilloscope


@pytest.mark.skipif(True, reason='Need brainamp device to test')
def test_brainampsocket():
    # in main App
    app = QtGui.QApplication([])

    """
    Data Acquisition Node
    """
    dev = BrainAmpSocket()
    dev.configure(brainamp_host='127.0.0.1', brainamp_port=51244)
    dev.outputs['signals'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    dev.outputs['triggers'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    dev.initialize() 
    

    """
    Filter Node
    """
    f1, f2 = 1., 20.
    sample_rate = dev.sample_rate
    
    coefficients = scipy.signal.iirfilter(2, [f1/sample_rate*2, f2/sample_rate*2],
                btype = 'bandpass', ftype = 'butter', output = 'sos')
    
    filter = SosFilter()
    filter.configure(coefficients = coefficients)
    filter.input.connect(dev.outputs['signals'])
    filter.output.configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    filter.initialize()

    """
    Oscilloscope Node
    """
    viewer = QOscilloscope()
    viewer.configure()
    # viewer.input.connect(filter.output)
    viewer.input.connect(filter.outputs['signals'])
    viewer.initialize()
    viewer.show()

    dev.start()
    viewer.start()
    filter.start()

    
    def terminate():
        viewer.stop()
        dev.stop()
        filter.stop()

        viewer.close()
        dev.close()
        filter.close()

        app.quit()
    
    # start for a while
    timer = QtCore.QTimer(singleShot=True, interval=5000)
    timer.timeout.connect(terminate)
    #~ timer.start()

    app.exec_()

    x = dev.get_posixtime_packet()[0]
    y = dev.get_posixtime_packet()[1]

    plotting(x[:len(y)], y[:len(x)])
    
    
def plotting(x, y):
    import matplotlib.pyplot as plt

    plt.plot(x,y)
    
    line = range(0,max(y))
    plt.plot(line, line, 'r')

    plt.show()


if __name__ == '__main__':
    test_brainampsocket()
