# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.

import time

from pyacq_ext.rawbufferdevice import RawDeviceBuffer
from pyacq.viewers import QOscilloscope
from PyQt5 import QtGui

import numpy as np
import mne

def test_npbufferdevice():
    app = QtGui.QApplication([])

    path = 'C:\\Users\\User\\Documents\\pybart\\eeg_data_sample\\CAPFE_0001.vhdr'
    
    # sigs = np.random.randn(2560, 7).astype('float64')
    raw = mne.io.read_raw_brainvision(path)
    sigsRaw = raw.get_data()
    
    sigsReshape = np.transpose(sigsRaw)
    
    sigs = sigsReshape*1000000/0.0488281

    dev = RawDeviceBuffer()
    dev.configure(nb_channel=16, sample_interval=0.001, chunksize=10, buffer=sigs)
    dev.output.configure(protocol='tcp', interface='127.0.0.1', transfermode='plaindata')
    dev.initialize()

    osc = QOscilloscope()
    osc.configure()
    osc.input.connect(dev.output)
    osc.initialize()
    
    dev.start()
    osc.start()
    osc.show()

    app.exec_()

if __name__ == '__main__':

    test_npbufferdevice()

 