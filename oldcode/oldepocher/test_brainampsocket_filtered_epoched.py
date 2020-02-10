# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.


import pytest
import scipy.signal
from pyqtgraph.Qt import QtCore, QtGui

import pyacq
import numpy as np
from pyacq import create_manager
from pyacq.devices.brainampsocket import BrainAmpSocket
from pyacq.dsp.sosfilter import SosFilter
from pyacq.viewers.qoscilloscope import QOscilloscope
from myextendedpyacq.epochermultilabel import EpocherMultiLabel
from myextendedpyacq.triggeremulator import TriggerEmulator


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
    
    filt = SosFilter()
    filt.configure(coefficients = coefficients)
    filt.input.connect(dev.outputs['signals'])
    filt.output.configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    filt.initialize()

    """
    Oscilloscope Node
    """
    viewer = QOscilloscope()
    viewer.configure()
    # viewer.input.connect(filt.output)
    viewer.input.connect(filt.outputs['signals'])
    viewer.initialize()
    viewer.show()

    """
    Triggers Laucher Node
    """
    te = TriggerEmulator()
    te.configure()
    te.outputs['triggers'].configure(protocol='tcp', transfermode='plaindata',)
    te.initialize()
    te.show()

    """
    Epocher Node
    """
    epocher = EpocherMultiLabel()
    epocher.configure()
    epocher.inputs['signals'].connect(filt.outputs['signals'])
    epocher.inputs['triggers'].connect(te.output)
    epocher.initialize()

    def on_new_chunk(name, new_chunk):
        print('Stack of {name} is full'.format(name = name))
        print(np.average(new_chunk, axis=1))

    epocher.new_chunk.connect(on_new_chunk)

    dev.start()
    viewer.start()
    filt.start()
    epocher.start()
    te.start()

    app.exec_()


if __name__ == '__main__':
    test_brainampsocket()
