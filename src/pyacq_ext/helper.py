# This class is used to create event that can be triggered by eventpoller, and listenned by mybpipeline

from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSignal

class Helper(QObject):
    resetSignal = pyqtSignal(bool)
    triggerSetupSignal = pyqtSignal(str)
    resultSignal = pyqtSignal()
    settingSignal = pyqtSignal(str)

