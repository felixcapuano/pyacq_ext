from pyqtgraph.Qt import QtCore, QtGui

import pyacq
from pyacq_ext.epochermultilabel import EpocherMultiLabel
from pyacq_ext.rawbufferdevice import RawDeviceBuffer
from pyacq_ext.brainvisionlistener import BrainVisionListener
from pyacq.viewers.qoscilloscope import QOscilloscope
from pyacq_ext.triggerhunter import TriggerHunter
from pyacq_ext.dataviewer import DataViewer


def test_brainampsocket():
    # in main App
    app = QtGui.QApplication([])

    """
    Trigger Hunter
    """
    trig = TriggerHunter()
    trig.configure()
    trig.outputs['triggers'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    trig.initialize()

    """
    Data Acquisition Node
    """
    dev = BrainVisionListener()
    dev.configure(brainamp_host='127.0.0.1', brainamp_port=51244)
    dev.outputs['signals'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    dev.outputs['triggers'].configure(protocol='tcp', interface='127.0.0.1',transfermode='plaindata',)
    dev.initialize()

    view = DataViewer()
    view.configure()
    view.inputs['sig1'].connect(dev.outputs['triggers'])
    view.inputs['sig2'].connect(trig.outputs['triggers'])
    view.initialize()


    trig.start()
#   devS.start()
    view.start()

    def terminate():
        trig.stop()
#       devS.stop()
        view.stop()

    # start for a while
    timer = QtCore.QTimer(singleShot=True, interval=5000)
    timer.timeout.connect(terminate)
    #~ timer.start()

    app.exec_()


if __name__ == '__main__':
    test_brainampsocket()
