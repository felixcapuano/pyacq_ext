# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Dycog\Dev_Python\_BciApps\Pypeline_MYB_Games\MYB_Games_Calib.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1296, 708)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.graphicsView = GraphicsLayoutWidget(self.centralwidget)
        self.graphicsView.setMinimumSize(QtCore.QSize(500, 0))
        self.graphicsView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.graphicsView.setObjectName(_fromUtf8("graphicsView"))
        self.horizontalLayout_2.addWidget(self.graphicsView)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.progressBar = QtGui.QProgressBar(self.centralwidget)
        self.progressBar.setMinimumSize(QtCore.QSize(40, 0))
        self.progressBar.setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);"))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setOrientation(QtCore.Qt.Vertical)
        self.progressBar.setTextDirection(QtGui.QProgressBar.BottomToTop)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout.addWidget(self.progressBar)
        self.progressBar_2 = QtGui.QProgressBar(self.centralwidget)
        self.progressBar_2.setMinimumSize(QtCore.QSize(40, 0))
        self.progressBar_2.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0);"))
        self.progressBar_2.setProperty("value", 0)
        self.progressBar_2.setTextVisible(False)
        self.progressBar_2.setOrientation(QtCore.Qt.Vertical)
        self.progressBar_2.setInvertedAppearance(False)
        self.progressBar_2.setTextDirection(QtGui.QProgressBar.BottomToTop)
        self.progressBar_2.setObjectName(_fromUtf8("progressBar_2"))
        self.verticalLayout.addWidget(self.progressBar_2)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout.addLayout(self.horizontalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1296, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuCalib = QtGui.QMenu(self.menubar)
        self.menuCalib.setObjectName(_fromUtf8("menuCalib"))
        self.menuCompute_Machine_Learning = QtGui.QMenu(self.menuCalib)
        self.menuCompute_Machine_Learning.setObjectName(_fromUtf8("menuCompute_Machine_Learning"))
        self.menuGame = QtGui.QMenu(self.menubar)
        self.menuGame.setObjectName(_fromUtf8("menuGame"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionStart_Pypeline = QtGui.QAction(MainWindow)
        self.actionStart_Pypeline.setObjectName(_fromUtf8("actionStart_Pypeline"))
        self.actionCalibVhdr = QtGui.QAction(MainWindow)
        self.actionCalibVhdr.setObjectName(_fromUtf8("actionCalibVhdr"))
        self.menuCompute_Machine_Learning.addAction(self.actionCalibVhdr)
        self.menuCalib.addAction(self.menuCompute_Machine_Learning.menuAction())
        self.menuGame.addAction(self.actionStart_Pypeline)
        self.menubar.addAction(self.menuCalib.menuAction())
        self.menubar.addAction(self.menuGame.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "P4", None))
        self.menuCalib.setTitle(_translate("MainWindow", "Calib", None))
        self.menuCompute_Machine_Learning.setTitle(_translate("MainWindow", "Compute Machine Learning", None))
        self.menuGame.setTitle(_translate("MainWindow", "Game", None))
        self.actionStart_Pypeline.setText(_translate("MainWindow", "Start Game ", None))
        self.actionCalibVhdr.setText(_translate("MainWindow", "Pick a *.vhdr file", None))

from pyqtgraph import GraphicsLayoutWidget

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

