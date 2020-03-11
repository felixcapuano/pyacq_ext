# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.


from pyqtgraph.Qt import QtCore, QtGui

import pyacq
from src.pyacq_ext.epochermultilabel import EpocherMultiLabel
from src.pyacq_ext.rawbufferdevice import RawDeviceBuffer
from src.pyacq_ext.brainvisionlistener import BrainVisionListener
from pyacq.viewers.qoscilloscope import QOscilloscope
from src.pyacq_ext.triggerhunter import TriggerHunter
from src.pyacq_ext.dataviewer import DataViewer


def test_brainampsocket():
    # in main App
    app = QtGui.QApplication([])


    # """
    # Data Acquisition Node
    # """
    # rawF = "C:\\Users\\User\\Documents\\pybart\\eeg_data_sample\\SAVEM_0004.vhdr"
    # devS = RawDeviceBuffer()
    # devS.configure(raw_file=rawF)
    # devS.outputs['signals'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    # devS.outputs['triggers'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    # devS.initialize()
    
    """
    Data Acquisition Node
    """
    dev = BrainVisionListener()
    dev.configure(brainamp_host='127.0.0.1', brainamp_port=51244)
    dev.outputs['signals'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    dev.outputs['triggers'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    dev.initialize()
    
    """
    Trigger Hunter
    """
    trig = TriggerHunter()
    trig.configure()
    trig.inputs['signals'].connect(dev.outputs['signals'])
    trig.outputs['triggers'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    trig.initialize()

    """
    Oscilloscope Node
    """
    viewer = QOscilloscope()
    viewer.configure()
    # viewer.input.connect(filter.output)
    viewer.input.connect(dev.outputs['signals'])
    viewer.initialize()
    viewer.show()

    view = DataViewer()
    view.configure()
    view.inputs['sig1'].connect(dev.outputs['triggers'])
    view.inputs['sig2'].connect(trig.outputs['triggers'])
    view.initialize()

    """
    Epocher Node
    """
    params = {
        "S  7":
        { 
            "right_sweep": 0.003,
            "left_sweep": 0.00,
            "max_stock": 1
        }
    }
    epocher = EpocherMultiLabel()
    epocher.configure(parameters = params)
    epocher.inputs['signals'].connect(dev.outputs['signals'])
    epocher.inputs['triggers'].connect(trig.outputs['triggers'])
    epocher.initialize()

    def on_new_epoch(label, epoch):
        print(label)
        pass

    epocher.new_chunk.connect(on_new_epoch)

    trig.start()
    dev.start()
    # devS.start()
    epocher.start()
    viewer.start()
    view.start()

    def terminate():
        trig.stop()
        dev.stop()
        # devS.stop()
        epocher.stop()
        viewer.stop()
        view.start()

        trig.close()
        dev.close()
        # devS.close()
        epocher.close()
        viewer.close()
        view.close()

        app.quit()
    
    # start for a while
    timer = QtCore.QTimer(singleShot=True, interval=5000)
    timer.timeout.connect(terminate)
    #~ timer.start()

    app.exec_()


if __name__ == '__main__':
    test_brainampsocket()
