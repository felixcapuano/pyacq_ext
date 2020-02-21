# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.

import os.path
import mne
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui

from pyacq.core import Node, register_node_type

_dtype_trigger = [('pos', 'int64'),
                ('points', 'int64'),
                ('channel', 'int64'),
                ('type', 'S16'),  # TODO check size
                ('description', 'S16'),  # TODO check size
                ]

class RawDeviceBuffer(Node):
    """A fake analogsignal device.
    
    This node streams data from a predefined buffer in an endless loop.
    """
    _output_specs = {
                        'signals': dict(
                            streamtype='analogsignal', 
                            shape=(-1, 16),
                            compression ='',
                            sample_rate =30.),
                        'triggers': dict(
                            streamtype = 'event',
                            dtype = _dtype_trigger,
                            shape = (-1,)),
                    }

    def __init__(self, **kargs):
        Node.__init__(self, **kargs)

    def configure(self, *args, **kwargs):
        """
        Parameters
        ----------
        nb_channel: int
            Number of output channels.
        sample_interval: float
            Time duration of a single data sample. This determines the rate at
            which data is sent.
        chunksize: int
            Length of chunks to send.
        buffer: array
            Data to send. Must have `buffer.shape[0] == nb_channel`.
        """
        return Node.configure(self, *args, **kwargs)

    def _configure(self, raw_file, chunksize=10):
        
        if not os.path.isfile(raw_file):
            raise ValueError("{} don't exist!".format(raw_file))

        extension = os.path.splitext(raw_file)[1]
        if extension == '.vhdr':
            raw = mne.io.read_raw_brainvision(raw_file)
        else:
            raise ValueError("{} file not supported".format(raw_file))
        
        self.nb_channel = raw.info['nchan']
        self.sample_interval = 1./raw.info['sfreq']
        self.chunksize = chunksize
        
        self.channel_names = raw.info['ch_names']
        
        self.outputs['signals'].spec['shape'] = (-1, self.nb_channel)
        self.outputs['signals'].spec['sample_rate'] = 1. / self.sample_interval
        
        self.buffer = np.transpose(raw.get_data())
        # TODO raise exception
        assert self.buffer.shape[1] == self.nb_channel, 'Wrong nb_channel'
        assert self.buffer.shape[0] % chunksize == 0, 'Wrong buffer.shape[0] not multiple chunksize'
        
        chan = 0
        for sensor in raw.info['chs']:
            self.buffer[:,chan] /= sensor['cal']*1e6
            chan +=1

        self.markers = self.load_markers(raw)

        self.length = self.buffer.shape[0]
        
        self.outputs['signals'].spec['dtype'] = self.buffer.dtype.name
    
    def load_markers(self, raw):
        markers_list = list()

        for m in raw.annotations:
            pos = int(m['onset']*1000)
            description, label = m['description'].split('/')

            markers_list.append((pos, 0, 0, description.encode(), label.encode()))

        del markers_list[0]

        return markers_list

    
    def after_output_configure(self, outputname):
        if outputname == 'signals':
            channel_info = [ {'name': self.channel_names[c]} for c in range(self.nb_channel) ]
            self.outputs[outputname].params['channel_info'] = channel_info

    def _initialize(self):
        self.head = 0
        ival = int(self.chunksize * self.sample_interval * 1000)
        self.timer = QtCore.QTimer(singleShot=False, interval=ival)
        self.timer.timeout.connect(self.send_data)
    
    def _start(self):
        self.head = 0
        self.timer.start()

    def _stop(self):
        self.timer.stop()
    
    def _close(self):
        pass
    
    def send_data(self):
        i1 = self.head%self.length
        self.head += self.chunksize
        i2 = i1 + self.chunksize
        self.outputs['signals'].send(self.buffer[i1:i2, :], index=self.head)

        markers_to_send = [mrk for mrk in self.markers if i1<mrk[0]<=i2]

        ## TODO Comm between epocher had to be improve useless data sended
        nb_marker = len(markers_to_send)

        markers = np.empty((nb_marker,), dtype=_dtype_trigger)
        for m in range(nb_marker):
            markers['pos'][m], markers['points'][m],markers['channel'][m] =  markers_to_send[m][0], 0, 0
            markers['type'][m], markers['description'][m] = markers_to_send[m][3], markers_to_send[m][4]

        self.outputs['triggers'].send(markers, index=nb_marker)

        

register_node_type(RawDeviceBuffer)
