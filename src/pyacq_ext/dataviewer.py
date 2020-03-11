from pyacq.core import Node, ThreadPollInput

class DataViewer(Node):
    """
    Monitors activity on an input stream and prints details about packets
    received.
    """
    _input_specs = {'sig1': dict(streamtype='events',  shape=(-1, )),
                    'sig2': dict(streamtype='events',  shape=(-1, ))}
    
    def __init__(self, **kargs):
        Node.__init__(self, **kargs)
    
    def _configure(self):
        pass

    def _initialize(self):
        # There are many ways to poll for data from the input stream. In this
        # case, we will use a background thread to monitor the stream and emit
        # a Qt signal whenever data is available.
        self.poller1 = ThreadPollInput(self.inputs['sig1'], return_data=True)
        self.poller2 = ThreadPollInput(self.inputs['sig2'], return_data=True)
        self.poller1.new_data.connect(self.data1_received)
        self.poller2.new_data.connect(self.data2_received)
        
    def _start(self):
        self.poller1.start()
        self.poller2.start()
        
    def data1_received(self, ptr, data):
        if ptr != 0:
            print("channel 1 pos: {}, label: {}".format(data[0][0], data[0][4]))
            pass

    def data2_received(self, ptr, data):
        print("channel 2 pos: {}, label: {}".format(data[0][0], data[0][4]))
        pass