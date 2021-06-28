# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.

import time

from pyacq import create_manager
from eeg_openBCIListener import OpenBCIListener, HAVE_PYSERIAL
from pyacq.viewers import QOscilloscope

from pyqtgraph.Qt import QtCore, QtGui

import pytest

@pytest.mark.skip(reason="need Device")
@pytest.mark.skipif(not HAVE_PYSERIAL, reason='no have pyserial')
def test_eeg_OpenBCI():
    # in main App
    app = QtGui.QApplication([])

    dev = OpenBCIListener()
    dev.configure(device_handle='/COM7')
    dev.outputs['signals'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    dev.outputs['aux'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    dev.initialize()

    viewer = QOscilloscope()
    viewer.configure()
    viewer.input.connect(dev.outputs['signals'])
    viewer.initialize()
    viewer.show()

    # dev.print_register_settings()
    dev.start()
    viewer.start()

    def terminate():
        viewer.stop()
        dev.stop()
        viewer.close()
        dev.close()
        app.quit()

    # start for a while
    timer = QtCore.QTimer(singleShot=True, interval=100000)
    timer.timeout.connect(terminate)
    timer.start()

    app.exec_()

if __name__ == '__main__':
    test_eeg_OpenBCI()
