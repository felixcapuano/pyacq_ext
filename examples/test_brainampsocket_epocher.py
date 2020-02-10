# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.


import pytest
from pyqtgraph.Qt import QtCore, QtGui

import pyacq
from pyacq_ext.epochermultilabel import EpocherMultiLabel
from pyacq import create_manager
from pyacq.devices.brainampsocket import BrainAmpSocket
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
    Oscilloscope Node
    """
    viewer = QOscilloscope()
    viewer.configure()
    # viewer.input.connect(filter.output)
    viewer.input.connect(dev.outputs['signals'])
    viewer.initialize()
    viewer.show()

    """
    Epocher Node
    """
    epocher = EpocherMultiLabel()
    epocher.configure()
    epocher.inputs['signals'].connect(dev.outputs['signals'])
    epocher.inputs['triggers'].connect(dev.outputs['triggers'])
    epocher.initialize()

    dev.start()
    epocher.start()
    viewer.start()
    
    def terminate():
        dev.stop()
        epocher.stop()
        viewer.stop()

        dev.close()
        epocher.close()
        viewer.close()

        app.quit()
    
    # start for a while
    timer = QtCore.QTimer(singleShot=True, interval=5000)
    timer.timeout.connect(terminate)
    #~ timer.start()

    app.exec_()

if __name__ == '__main__':
    test_brainampsocket()
