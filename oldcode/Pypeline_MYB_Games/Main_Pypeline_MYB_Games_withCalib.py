   # -*- coding: utf-8 -*-

import sys
import os
import numpy as np

from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
sys.path.append(str('..\..\python_pyacq'))
import pyacq as pyacq

import pyacq.gui
import neo

import fileinput
import re
import time

import scipy.io 

import Player_MYB_Pypeline

sys.path.append('..\..\python_crnl_bci\PyLyonBci')

import pylyonbci
from pylyonbci import pyrte

from pylyonbci.CustomTermcolor import *



#import ipdb

import pickle #to save params data in a file (python basic serialisation package)
import zmq

import subprocess
import datetime
import colorsys

import MYB_Games_Calib_ui as qt_design








################################################################################
def debug():
    QtCore.pyqtRemoveInputHook()
    from ipdb import set_trace
    set_trace()
################################################################################



################################################################################
class SubProcessThread(QtCore.QThread):
    """
    subprocess.call() is blocking, this is a good technique to use it and send a signal when subprocess returned
    """
    signal_process_returned = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None, subprocess_call_args=([], '')):
        QtCore.QThread.__init__(self, parent)
        self.subprocess_call_args = subprocess_call_args

    def run(self):
        """
        QThread abstract function to overload.
        """
        p4 = subprocess.call(self.subprocess_call_args[0], cwd=self.subprocess_call_args[1], shell=True)
        self.signal_process_returned.emit(True)
################################################################################





class MyOscilloscope(pyacq.gui.Oscilloscope):
    """
    a more styled oscilloscope and a simple inheritance example
    """
    def __init__(self, title, qicon, background_qcolor, pen_color_rgb, *args, **kwargs):
        pyacq.gui.Oscilloscope.__init__(self, *args, **kwargs)


        self.setWindowTitle(title)

        self.mainlayout.setSpacing(0)
        self.mainlayout.setMargin(0)

        self.setWindowIcon(qicon)

        #set gradient color for background color
        gradient = QtGui.QLinearGradient(QtCore.QRectF(self.graphicsview.rect()).topLeft(), QtCore.QRectF(self.graphicsview.rect()).bottomLeft())
        gradient.setColorAt(0, background_qcolor)
        gradient.setColorAt(1, QtCore.Qt.black)

        self.graphicsview.setBackground(QtGui.QBrush(gradient))

        hue, sat, val = colorsys.rgb_to_hsv(*pen_color_rgb)
        for index, curve in enumerate(self.curves):
            sat_var = (float(index)/len(self.curves))
            curve.setPen(pg.hsvColor(hue, sat_var, val))
            
            
            
            
            
            
class OnePlayerGame(QtGui.QMainWindow, qt_design.Ui_MainWindow):
    """
    instanciates one OnePlayerGame and one zmq publisher socket to send both classified answers to the MYB Games stimulator.
    """
    def __init__(self, parent=None):

        QtGui.QMainWindow.__init__(self, parent) #initialize inheritance

        self.setupUi(self) #initialize qt_design.Ui_MainWindow
                            #see qt_design file built from pyuic4 (qt designer)
                            # exec cmd: pyuic4 P4.ui -o P4_ui.py


        app_icon = QtGui.QIcon()
        app_icon.addFile('./MYB_logo.png', QtCore.QSize(300, 300))
        self.setWindowIcon(app_icon)

        self._init_zmq_pub()
       
        
        self.player0 = Player_MYB_Pypeline.Player_MYB_Pypeline(
                                                    nom_de_code_du_sujet='PLAYER', 
                                                    Brainvision_IP_Hostname = 'localhost',
                                                    displayDevice=0) # = 0 laptop only, =1 extended display

        self.player0.signal_new_LikelihoodFunction_result.connect(self.pub_send_Likelihood)
        

        self.calib_filename0 = None
        self.savefile= None
        self.player0_EEG_has_chosen = False
        self.player0_EEG_chosen_item = None
        self.player0_EEG_entropy = None
        self.player0_EEG_proba = None
        
        

        self.oscillo0 = MyOscilloscope(
                                title='Player',
                                qicon=app_icon,
                                background_qcolor=QtCore.Qt.red,
                                pen_color_rgb=(1, 0, 0),
                                stream=self.player0._bandpass_filter.out_stream
        )
        self.oscillo0.auto_gain_and_offset(mode=1)
        self.oscillo0.set_params(xsize=10.)
        self.oscillo0.show()

        
        
        
        self.actionCalibVhdr.triggered.connect(self.user_choice_machine_learning)
        self.actionStart_Pypeline.triggered.connect(self.start_Pypeline)
        

        self._player0_score_progressbar = 0

        
        pg_layout = self.graphicsView.ci
        self.plot_label0 = pg_layout.addLabel(angle=-90)
        self.plot_item0 = pg_layout.addPlot()


        self.animation_score_player0 = QtCore.QPropertyAnimation(self, "player0_score_progressbar")

        self.progressBar.setTextDirection(QtGui.QProgressBar.BottomToTop)

        self.player0.start_watching_signal()

        
#_______________________________________________________________________________
    def _init_zmq_pub(self):
        self.context_pub = zmq.Context()
        self.zmq_pub = self.context_pub.socket(zmq.REP)
        self.zmq_pub.bind('tcp://127.0.0.1:5555')
        
        self.TabLF = ""
        self.NbFlashs = 0
        self.CountEpoch = 0
        
#_______________________________________________________________________________
    @QtCore.pyqtProperty(int)
    def player0_score_progressbar(self):
        return self._player0_score_progressbar
#_______________________________________________________________________________
    @player0_score_progressbar.setter
    def player0_score_progressbar(self, value):
        self._player0_score_progressbar = value
        self.progressBar.setValue(self._player0_score_progressbar)
#_______________________________________________________________________________



#_______________________________________________________________________________
    @QtCore.pyqtSlot(np.ndarray)
    def pub_send_Likelihood(self,Likelihood):
        """
        within a QtSlot function, use sender() method returns a ref on signal sender instance object (the object connected to this slot).
        this way, we can have a single slot function (callback function) for several objects. 
        (both player1 and player2's signal_new_classifier_result are connected to this slot)
        
        """
        
        sender = self.sender()
        
        self.player0_Likelihood = Likelihood
#        LikelihoodCurr =  "{0:.6f}".format(float(self.player0_Likelihood[0])) + "\t" +  "{0:.6f}".format(float(self.player0_Likelihood[1])) + "\n"


        
        
        self.TabLF = self.TabLF + "{0:.6f}".format(float(self.player0_Likelihood[0])) + ";"
        self.TabLF = self.TabLF + "{0:.6f}".format(float(self.player0_Likelihood[1])) + ";"
        
        self.CountEpoch = self.CountEpoch + 1
        
#        print(".CountEpoch",self.CountEpoch)
        
        
        
        try:
            self.message = self.zmq_pub.recv(flags=zmq.NOBLOCK)
            print("Message Received EEG Epoch  ", self.message)
            print("CountEpoch current  ", self.CountEpoch)

            if (int(self.message)>0 and int(self.message)<120):
                self.NbFlashs = int(self.message);
                self.message = ""
                
        except zmq.ZMQError:
            self.message = ""
        
        if ((self.NbFlashs>0) and (self.CountEpoch == self.NbFlashs)):
            scipy.io.savemat('D:\Dycog\Dev_Python\LF.mat', mdict={'LF': self.TabLF[0:-1] })
#            print('           ----------------               Send to unity (EEG Epoch)')
            TabXY = np.ones(self.NbFlashs*24)*800
            self.TabGaze = ""
            for i in range(len(TabXY)):
                self.TabGaze = self.TabGaze + "{0:.6f}".format(TabXY[i]) + ";" 
        
            # MSGRES = self.zmq_pub.send('100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100;100' + '|' + self.TabLF[0:-1])
            MSGRES = self.zmq_pub.send(self.TabGaze[0:-1] + '|' + self.TabLF[0:-1])
            print('           ----------------               Send to unity (EEG Epoch) :', MSGRES)
            self.TabGaze = ""
            self.TabLF = ""
            self.CountEpoch =0
            self.NbFlashs =0
                


        




#_______________________________________________________________________________
    def start_Pypeline(self):
                    
                  
        self.player0.stop_online()
        
             
        
        print " \n\n\n****************************     PIPELINE STARTED     ****************************\n\n"
       
#        self.player0.stop_watching_signal()
        self.player0.start_online()
        self.player0_has_chosen = False
        self.player0_ChoiceFromEEG  = True
        
        
        
    


#_______________________________________________________________________________
    def stop_online(self):
        self.savefile.close()
        self.player0.stop_online()
#        self.player0.start_watching_signal()

#_______________________________________________________________________________
    def closeEvent(self, event):
        """
        QtGui.QMainWindow abstract function to override. (callback when the main window widget close signal is sent: if user press close button)
        
        """
        try:
            self.stop_calib()
        except:
            pass

        try:
            self.stop_online()
        except:
            pass

        self.oscillo0.close()

        try:
            self.player0.stop_watching_signal()

        except:
            pass
#_______________________________________________________________________________
    def user_choice_machine_learning(self):
#        self.player0.stop_watching_signal()
#        self.player0.start_watching_signal()
        
        calib_filepath0 = QtGui.QFileDialog.getOpenFileName(
                                                        self, 
                                                        caption='Choose calibration .vhdr file', 
                                                        directory=os.path.join(os.getcwd(), 'C:/Vision/Raw Files/'),
                                                        filter='*.vhdr'
        )       
        (dirname0, self.calib_filename0) = os.path.split(str(calib_filepath0))
        
        self.TemplateRiemann=self.player0.get_learning(dirname0, self.calib_filename0)


        self._display_machine_learning_curves()
#_______________________________________________________________________________
 
        
        
        
        
#_______________________________________________________________________________
    def _display_machine_learning_curves(self):
        pg_layout = self.graphicsView.ci

        self.plot_label0.setText(
                            'Player <b> Accuracy : {} %</b>'.format(
                                                        round(self.TemplateRiemann['AccP300'][...])))
        self.plot_item0.clear()
        self.player0.plot_machine_learning(self.calib_filename0,self.plot_item0, color_rgb=(255, 0, 0))

#        anim_step_duration = 10 #ms
#
#        self.animation_score_player0.setDuration(self.player0.score_LOO_crossvalidation*anim_step_duration)
#        self.animation_score_player0.setStartValue(QtCore.QVariant(0))
#        self.animation_score_player0.setEndValue(QtCore.QVariant(round(self.player0.score_LOO_crossvalidation)))

        

#===============================================================================
def main():

    app = QtGui.QApplication([])
    win = OnePlayerGame()
    win.show()
    sys.exit(app.exec_())
#    proto.close_all()


if __name__ == '__main__':
    print 'starting main: PID :', os.getpid()
    main()            
            
            
