import pdb

import numpy as np
import pyqtgraph as pg
from pyacq.core import Node, ThreadPollInput
from pyqtgraph.Qt import QtCore
from pyqtgraph.util.mutex import Mutex


class ThreadPollInputUntilPosWaited(ThreadPollInput):
    """
    Thread waiting a futur pos in a stream.
    """
    pos_reached = QtCore.pyqtSignal(int, object)

    def __init__(self, input_stream,  **kargs):
        ThreadPollInput.__init__(self, input_stream, **kargs)

        self.locker = Mutex()
        self.pos_waited = 0

    def set_trigger(self, pos_waited):
        self.pos_waited = pos_waited

    def process_data(self, pos, data):
        with self.locker:

            if self.pos_waited == 0:
                return

            if pos >= self.pos_waited:
                self.pos_reached.emit(pos, self)
                print("position reached")


class EpocherMultiLabel(Node,  QtCore.QObject):

    _input_specs = {'signals': dict(streamtype='signals'),
                    # dtype ='int64',
                    'triggers': dict(streamtype='events',  shape=(-1, )),
                    }
    _output_specs = {}

    _params_ex = {
        'left_sweep': -0.2,
        'right_sweep': 0.6,
        'stack_size': 2,
    }
    _default_params = {
        'S  1': _params_ex,
        'S  2': _params_ex,
        'S  3': _params_ex,
        'S  4': _params_ex,
        'S  5': _params_ex,
        'S  6': _params_ex,
        'S  7': _params_ex,
    }

    # ?
    new_chunk = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, **kargs):
        QtCore.QObject.__init__(self, parent)
        Node.__init__(self, **kargs)

    def _configure(self, parameters=_default_params):
        self.parameters = parameters

    def after_input_connect(self, inputname):
        if inputname == 'signals':
            self.nb_channel = self.inputs['signals'].params['shape'][1]
            self.sample_rate = self.inputs['signals'].params['sample_rate']
        elif inputname == 'triggers':
            pass

    def _initialize(self):
        self.trig_poller = ThreadPollInput(
            self.inputs['triggers'], return_data=True)
        self.trig_poller.new_data.connect(self.on_new_trig)

        self.initialize_stack()

    def _start(self):
        self.trig_poller.start()

    def _stop(self):
        self.trig_poller.stop()
        self.trig_poller.wait()

    # TODO ValueError: not enough values to unpack (expected 2, got 1). Check logs.txt
    def on_new_trig(self, trig_num, trig_indexes):

        for pos, pts, channel, classification, name in trig_indexes:

            print('Just captured new triger : {}'.format(trig_indexes))
            print('Position : {}'.format(pos))

            thread_waiting = ThreadPollInputUntilPosWaited(
                self.inputs['signals'])
            thread_waiting.set_trigger(pos+3000)
            thread_waiting.pos_reached.connect(self.on_pos_reached)
            thread_waiting.start()

            self.thread_waiting_list.append(thread_waiting)

    def on_pos_reached(self, pos, thread):
        thread.stop()
        thread.wait()
        print('End thread at position {}!'.format(pos))

    def initialize_stack(self):
        for trigger_parameter in self.parameters.values():
            trigger_parameter['left_limit'] = int(
                trigger_parameter['left_sweep']*self.sample_rate)
            trigger_parameter['right_limit'] = int(
                trigger_parameter['right_sweep']*self.sample_rate)

            trigger_parameter['size'] = trigger_parameter['right_limit'] - \
                trigger_parameter['left_limit']

        self.thread_waiting_list = []
