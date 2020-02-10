from pyqtgraph.Qt import QtGui
from pyacq_ext.nodeweb import NodeWeb


def on_new_chunk(label, chunk):
    print('YES')

if __name__ == '__main__':    
    app = QtGui.QApplication([])

    ex = NodeWeb()
    ex.configuration_amp(on_new_chunk)
    ex.start_node()

    app.exec_()