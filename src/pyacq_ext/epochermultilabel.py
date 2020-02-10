import pdb

import numpy as np
import pyqtgraph as pg
from pyacq.core import Node, ThreadPollInput
from pyqtgraph.Qt import QtCore
from pyqtgraph.util.mutex import Mutex


class ThreadPollInputUntilPosWaited(ThreadPollInput):
    """Thread waiting a futur pos in a stream."""
    
    pos_reached = QtCore.pyqtSignal(int, str)

    def __init__(self, input_stream,  **kargs):
        ThreadPollInput.__init__(self, input_stream, **kargs)

        self.locker = Mutex()
        self.pos_waited_list = []

    def append_limit(self, label, pos_waited):
        self.pos_waited_list.append((label, pos_waited))

    def reset(self):
        with self.locker:
            self.pos_waited_list = []

    def process_data(self, pos, data):
        with self.locker:

            if len(self.pos_waited_list) == 0:
                return

            for pos_waited, label in self.pos_waited_list:
                if pos >= pos_waited:
                    self.pos_reached.emit(pos_waited, label)
            self.pos_waited_list = [
                pos_waited for pos_waited in self.pos_waited_list if pos < pos_waited[0]]


class EpocherMultiLabel(Node,  QtCore.QObject):
    """Node that accumulate in a ring buffer chunk of a multi signals on trigger events configurable.

    This Node have no output.

    On each new chunk this new_chunk is emmited.
    Note that this do not occurs on new trigger but a bit after when the right_sweep is reached on signals stream.

    """
    _input_specs = {'signals': dict(streamtype='signals'),
                    'triggers': dict(streamtype='events',  shape=(-1, )),
                    }
    _output_specs = {}

    _params_ex = {
        'left_sweep': 0.002,
        'right_sweep': 0.003,
        'max_stock': 1,
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

    new_chunk = QtCore.pyqtSignal(str, np.ndarray)

    def __init__(self, parent=None, **kargs):
        QtCore.QObject.__init__(self, parent)
        Node.__init__(self, **kargs)

    def _configure(self, parameters=_default_params, max_xsize=2.):
        """Parameters
        ----------
        parameters : dict
            The parameters that configure each triggers event :
            {
                trigger_name (str) : {
                    left_sweep -- the left shift (float),
                    right_sweep -- the left shift (float),
                    max_stock -- the stack maximum (int),
                }
                ...
            } 
        max_xsize: int, optional
            The maximum sample chunk size

        """
        self.parameters = parameters
        self.max_xsize = max_xsize

        self._dict_format()

    def after_input_connect(self, inputname):
        if inputname == 'signals':
            self.nb_channel = self.inputs['signals'].params['shape'][1]
            self.sample_rate = self.inputs['signals'].params['sample_rate']

            self.configure_triggers_parameters()
        elif inputname == 'triggers':
            pass

    def _initialize(self):
        buf_size = int(
            self.inputs['signals'].params['sample_rate'] * self.max_xsize)
        self.inputs['signals'].set_buffer(
            size=buf_size, axisorder=[1, 0], double=True)

        self.trig_poller = ThreadPollInput(
            self.inputs['triggers'], return_data=True)
        self.trig_poller.new_data.connect(self.on_new_trig)

        self.pos_waiter = ThreadPollInputUntilPosWaited(self.inputs['signals'])
        self.pos_waiter.pos_reached.connect(self.on_pos_reached)

        self.initialize_storage()

    def _start(self):
        self.trig_poller.start()
        self.pos_waiter.start()

    def _stop(self):
        self.trig_poller.stop()
        self.trig_poller.wait()

        self.pos_waiter.stop()
        self.pos_waiter.wait()

    def on_new_trig(self, trig_num, trig_indexes):
        for pos, pts, channel, classification, label in trig_indexes:
            print('Just captured new triger : {}, Position : {}'.format(
                trig_indexes, pos))

            label = label.decode()
            if label in self.parameters.keys():
                pos_waited = pos + self.parameters[label]['right_limit']
                self.pos_waiter.append_limit(pos_waited, label)

    def on_pos_reached(self, pos, label):
        print('{} reach the pos at {}!'.format(label, pos))

        size_stock = self.parameters[label]['size']
        epoch = self.inputs['signals'].get_data(
            pos - size_stock, pos).transpose()

        if epoch is not None:
            weight = self.epoch_storage[label]['weight']

            self.epoch_storage[label]['stock'][weight, :, :] = epoch
            self.epoch_storage[label]['weight'] += 1

        for label in self.epoch_storage.keys():
            if self.epoch_storage[label]['weight'] >= self.parameters[label]['max_stock']:
                self.new_chunk.emit(label, self.epoch_storage[label]['stock'])
                self.reset_stock(label)

    def configure_triggers_parameters(self):
        for trigger_parameter in self.parameters.values():
            trigger_parameter['left_limit'] = int(
                trigger_parameter['left_sweep']*self.sample_rate) * -1
            trigger_parameter['right_limit'] = int(
                trigger_parameter['right_sweep']*self.sample_rate)

            trigger_parameter['size'] = trigger_parameter['right_limit'] - \
                trigger_parameter['left_limit']

    def initialize_storage(self):
        self.epoch_storage = {}
        for label in self.parameters.keys():
            self.epoch_storage[label] = {}
            self.reset_stock(label)
            self.pos_waiter.reset()

    def reset_stock(self, label):
        parameter = self.parameters[label]
        self.epoch_storage[label]['stock'] = np.zeros(
            (parameter['max_stock'], self.nb_channel, parameter['size']), dtype=self.inputs['signals'].params['dtype'])
        self.epoch_storage[label]['weight'] = 0

    def _dict_format(self):
        if type(self.parameters) is not dict:
            raise Exception('Argument :parameters: has to be type `dict`')

        for params in self.parameters.values():
            if params.keys() != self._params_ex.keys():
                raise Exception(':parameters: wrong format')
