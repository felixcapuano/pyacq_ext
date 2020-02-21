# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.

import time

import mne
import numpy as np
from mne.io.brainvision.brainvision import _read_annotations_brainvision
from PyQt5 import QtGui

from pyacq.viewers import QOscilloscope
from pyacq_ext.rawbufferdevice import RawDeviceBuffer
from pyacq_ext.dataviewer import DataViewer


def test_npbufferdevice():
    pathHDR = 'E:\Documents\Dev\python\pybart_project\pybart\eeg_data_sample\CAPFE_0002.vhdr'
    pathMRK = 'E:\Documents\Dev\python\pybart_project\pybart\eeg_data_sample\CAPFE_0002.vmrk'

    # raw = mne.io.read_raw_brainvision(pathHDR)
    # markers = read_annotations(raw)
    
    # i1, i2 = 20000,20600
    # mrks = [mrk for mrk in markers if i1<mrk[0]<i2]

    # print(mrks)
    
    pyacq_node(pathHDR)

def read_annotations(raw):
    markers_list = list()

    for m in raw.annotations:
        pos = int(m['onset']*1000)
        description, label = m['description'].split('/')

        markers_list.append((pos, 0, 0, description.encode(), label.encode()))

    del markers_list[0]

    return np.array(markers_list)

def pyacq_node(path):
    app = QtGui.QApplication([])

    dev = RawDeviceBuffer()
    dev.configure(raw_file=path, chunksize=10)
    dev.outputs['signals'].configure(protocol='tcp', interface='127.0.0.1', transfermode='plaindata')
    dev.outputs['triggers'].configure(protocol='tcp', interface='127.0.0.1', transfermode='plaindata')
    dev.initialize()

    osc = QOscilloscope()
    osc.configure()
    osc.input.connect(dev.outputs['signals'])
    osc.initialize()

    # tv = DataViewer()
    # tv.configure()
    # tv.input.connect(dev.outputs['triggers'])
    # tv.initialize()
    
    dev.start()
    osc.start()
    osc.show()
    # tv.start()

    app.exec_()

if __name__ == '__main__':

    test_npbufferdevice()
