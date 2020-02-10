# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.


import numpy as np
import pyacq
import pytest
from pyacq import create_manager
from pyacq.core.node import Node
from pyacq.core.tools import ThreadPollInput
from pyacq.devices.brainampsocket import BrainAmpSocket
from pyacq.viewers.qoscilloscope import QOscilloscope
from pyqtgraph.Qt import QtCore, QtGui

from myextendedpyacq.epochermultilabel import EpocherMultiLabel
from myextendedpyacq.triggeremulator import TriggerEmulator
from myextendedpyacq.noisegenerator import NoiseGenerator



def test_brainampsocket():
    # in main App
    app = QtGui.QApplication([])

    """
    Triggers Laucher Node
    """
    te = TriggerEmulator()
    te.configure()
    te.outputs['triggers'].configure(protocol='tcp', transfermode='plaindata',)
    te.initialize()
    te.show()

    """
    Noise Generator Node
    """
    ng = NoiseGenerator()
    ng.configure(number_channel=16)
    ng.output.configure(protocol='tcp', transfermode='plaindata')
    ng.initialize()

    """
    Oscilloscope Node
    """
    viewer = QOscilloscope()
    viewer.configure()
    viewer.input.connect(ng.output)
    viewer.initialize()
    viewer.show()

    """
    Epocher Node
    """
    params = {'S  1': {
        'left_sweep': 0.002,
        'right_sweep': 0.003,
        'max_stock': 1,
    }}

    epocher = EpocherMultiLabel()
    epocher.configure(parameters=params)
    epocher.inputs['signals'].connect(ng.output)
    epocher.inputs['triggers'].connect(te.output)
    epocher.initialize()

    def on_new_chunk(name, new_chunk):
        print('Stack of {name} is full'.format(name=name))
        
        print(np.average(new_chunk, axis=1))
        

    epocher.new_chunk.connect(on_new_chunk)

    epocher.start()
    viewer.start()
    te.start()
    ng.start()

    app.exec_()


if __name__ == '__main__':
    test_brainampsocket()
