import datetime
import os
import pickle
import sys

import numpy as np
import pyqtgraph as pg
import scipy.io
from scipy.linalg import eigvalsh

import h5py
import pyacq as pyacq
import pyacq.gui
import pylyonbci
import RiemannTemplateLearn
from pathlib2 import Path
from pylyonbci import pyrte
from pylyonbci.CustomTermcolor import *
from PyQt4 import QtCore, QtGui

sys.path.append('..\..\python_crnl_bci\PyLyonBci')







class Player_MYB_Pypeline(QtCore.QObject): #inherits QObject to send signals

    signal_new_LikelihoodFunction_result = QtCore.pyqtSignal(np.ndarray)

    #_______________________________________________________________________________
    def __init__(self, 
                nom_de_code_du_sujet, 
                Brainvision_IP_Hostname,
                displayDevice,
                parent=None):
        """
        begin any pyacq protocol by instanciating an pyacq.StreamHandler
        """
        QtCore.QObject.__init__(self, parent)
        self._streamhandler = pyacq.StreamHandler()

        self._trial_counter = 0

        self.nom_de_code_du_sujet = nom_de_code_du_sujet
        self.Brainvision_IP_Hostname = Brainvision_IP_Hostname
        self.displayDevice = displayDevice
        self.Time_win_sec_EEG = 0.600
        
        self._init_protocol_objects()
        
#_______________________________________________________________________________
    def get_learning(self, data_directory=None, filename=None):
        """ 
        looks for learning parameters file
        if can't find it, compute it with self._compute_learning
        """

        my_file = Path(os.path.join(os.getcwd(), 'TemplateRiemann', 'Template_{}.h5'.format(filename)))
        
        if my_file.is_file():
            self.TemplateRiemann = self._init_Template_Riemann(os.path.join(os.getcwd(), 'TemplateRiemann', 'Template_{}.h5'.format(filename)))
        else:
            self.TemplateRiemann = self._compute_learning(data_directory=data_directory,filename=filename)
	
        return self.TemplateRiemann
#_______________________________________________________________________________
    def _compute_learning(self, data_directory, filename):
        """
        compute Template
        compute machine learning: classifier parameters
        save learning parameters in *.h5 file
        """
        self.TemplateRiemann = RiemannTemplateLearn.RiemannTemplateLearn(os.path.join(data_directory, filename), analysis_time_window_sec=self.Time_win_sec_EEG, threshold_rejection=0.15)
        pyrte.utils.writeH5FileTemplate(self.TemplateRiemann,os.path.join(os.getcwd(), 'TemplateRiemann', 'Template_{}.h5'.format(filename)))
        #l_TemplateRiemann = self._init_Template_Riemann(os.path.join(os.getcwd(), 'TemplateRiemann', 'Template_{}.h5'.format(filename)))
        return self.TemplateRiemann

#_______________________________________________________________________________
    def plot_machine_learning(self, filename, pyqtgraph_plot_item, color_rgb ):
        """
        plot machine learning curves in a pyqtgraph plot item.
        feed a pyqtgraph plotItem ref for argument.
        """
        def _mean_var_plot(pyqtgraph_plot_item, mean, variance, pencolor=(255, 255, 255), brushcolor=(255, 255, 255, 100)):
    #        pyqtgraph_plot_item.clear()
            mean_plot = pyqtgraph_plot_item.plot(mean, pen=pencolor, antialias=True)
            mean_variance_plot1 = pyqtgraph_plot_item.plot(mean + np.sqrt(variance), pen=brushcolor)
            mean_variance_plot2 = pyqtgraph_plot_item.plot(mean - np.sqrt(variance), pen=brushcolor)
            mean_variance_plot1.curve.path = mean_variance_plot1.curve.generatePath(*mean_variance_plot1.curve.getData())
            mean_variance_plot2.curve.path = mean_variance_plot2.curve.generatePath(*mean_variance_plot2.curve.getData())
            mean_variance_fill = pg.FillBetweenItem(mean_variance_plot1, mean_variance_plot2, brush=brushcolor)
            pyqtgraph_plot_item.addItem(mean_variance_fill)
       
        print self.TemplateRiemann['mu_Epoch_T'].shape[0]
        if self.TemplateRiemann['mu_Epoch_T'].shape[0]==16:
            target_mean         = self.TemplateRiemann['mu_Epoch_T'][3,:]
            target_variance     = self.TemplateRiemann['var_Epoch_T'][3,:]
            not_target_mean     = self.TemplateRiemann['mu_Epoch_NT'][3,:]
            not_target_variance = self.TemplateRiemann['var_Epoch_NT'][3,:]
        else:
            target_mean         = self.TemplateRiemann['mu_Epoch_T'][13,:]
            target_variance     = self.TemplateRiemann['var_Epoch_T'][13,:]
            not_target_mean     = self.TemplateRiemann['mu_Epoch_NT'][13,:]
            not_target_variance = self.TemplateRiemann['var_Epoch_NT'][13,:]       
       
       
#        self.TemplateRiemann = self._init_Template_Riemann(os.path.join(os.getcwd(), 'TemplateRiemann', 'Template_{}.h5'.format(filename)))
#        if self.TemplateRiemann['mu_Epoch_T'].shape[1]==16:
#            target_mean         = self.TemplateRiemann['mu_Epoch_T'][3,:]
#            target_variance     = self.TemplateRiemann['var_Epoch_T'][3,:]
#            not_target_mean     = self.TemplateRiemann['mu_Epoch_NT'][3,:]
#            not_target_variance = self.TemplateRiemann['var_Epoch_NT'][3,:]
#        else:
#            target_mean         = self.TemplateRiemann['mu_Epoch_T'][13,:]
#            target_variance     = self.TemplateRiemann['var_Epoch_T'][13,:]
#            not_target_mean     = self.TemplateRiemann['mu_Epoch_NT'][13,:]
#            not_target_variance = self.TemplateRiemann['var_Epoch_NT'][13,:]
#            
        
        
        
        
        _mean_var_plot(pyqtgraph_plot_item, not_target_mean, not_target_variance)
        _mean_var_plot(pyqtgraph_plot_item, target_mean, target_variance, pencolor=color_rgb, brushcolor=color_rgb+(100,))

		
#_______________________________________________________________________________
    def _init_EEG_Epoching(self):
        offset = 0.08
        self.params_EEG = {
                            'col1': {
                                    'code': 1, #'1',
                                    'count': 1,
                                    'left_sweep': offset,
                                    'right_sweep':self.Time_win_sec_EEG + offset+0.001,                                    
                                    },
                          }
        
        self._multi_epoch_EEG = pylyonbci.MultiMeanEpoch.MultiMeanEpoch( #if it is another calibration this might kill the old reference for a new one
                                                    parent=self,
                                                    sig_stream=self._bandpass_filter.out_stream, 
                                                    trig_stream=self.RenameTriggerStream.out_stream, #case brainamp with events on paralell port
                                                    params_by_labels=self.params_EEG,
                                                    key='description')
        
        self._multi_epoch_EEG.signal_all_mean_epoch.connect(self.on_all_mean_epoch_EEG)
        self._multi_epoch_EEG.signal_new_mean_epoch.connect(self.on_epoch_mean_EEG) #
        
                
        
        
        
#_______________________________________________________________________________
    def _init_Template_Riemann(self,Template_H5Filename):
        self.f = h5py.File(Template_H5Filename, 'r')
        
        print('## Lecture du fichier {}'.format(Template_H5Filename))
        
        self.dict = {}
        for element in self.f:
            groupe = self.f[element]
                        
            for element in groupe:
                self.dict[element] = groupe[element]
                
        TemplateParams = self.dict
#        print('template',TemplateParams['mu_Epoch_T'][...])

        return TemplateParams
        
        
        
        
        
        


#_______________________________________________________________________________
    def _init_data_acquisition_device_brainvision(self,brainVision_host):
        brainvision_device = pyacq.BrainvisionSocket(streamhandler=self._streamhandler)
        brainvision_device.configure(
                    buffer_length=64,
                    brain_host=brainVision_host,
                    brain_port=51244)
        brainvision_device.initialize()

        return brainvision_device   
        
  
                
                

          

#_______________________________________________________________________________
    def _init_protocol_objects(self):
        """
        init pyacq objects needed for the protocol
        function gotta be called after pyacq.StreamHandler() and data driver instanciation
        """

        self._data_acquisition_device = self._init_data_acquisition_device_brainvision(self.Brainvision_IP_Hostname)

        self._bandpass_filter = pyacq.BandPassFilter(
                                                stream=self._data_acquisition_device.streams[0],
                                                streamhandler=self._streamhandler)
        self._bandpass_filter.set_params(
                                    f_start=.5,
                                    f_stop=20.)
                                    
        self.RenameTriggerStream = pyacq.RenameTriggerStream(streamhandler=self._streamhandler,
                                                              sig_stream=self._data_acquisition_device.streams[0], 
                                                                trig_stream=self._data_acquisition_device.streams[1]
                                                                )                            
                                    
        
        self._init_EEG_Epoching()
        
        self.TemplateRiemann = self._init_Template_Riemann('D:\Dycog\Dev_Python\_BciApps\Pypeline_MYB_Games\TemplateRiemann\Template.h5')
        
#        print "mu_rTNT_T", self.TemplateRiemann['mu_rTNT_T'][...]
#        print "mu_rTNT_NT", self.TemplateRiemann['mu_rTNT_NT'][...]
#        print "sigma_rTNT_T", self.TemplateRiemann['sigma_rTNT_T'][...]
#        print "sigma_rTNT_NT", self.TemplateRiemann['sigma_rTNT_NT'][...]


#_______________________________________________________________________________
    @QtCore.pyqtSlot()
    def on_all_mean_epoch_EEG(self):
        self._multi_epoch_EEG.global_reset_trial()
#_______________________________________________________________________________
    @QtCore.pyqtSlot()
    def on_all_mean_epoch_SMI(self):
        self._multi_epoch_EyeTracker.global_reset_trial()


#_______________________________________________________________________________
    @QtCore.pyqtSlot(str) #use this for connect_four with dynamic bayesian classification
    def on_epoch_mean_EEG(self, label):
        """
        classifies new ERP according to learning parameters and bayes priors for connect_four with dynamic bayesian classification
        """
        #find the epoch data corresonding to this label.
        label = str(label) 
        custom_print_in_yellow(self, 'EPOCH EEG label', label)
        #C4 label corresponds to a column index.
#        params_for_epoch_label = self.params_EEG[label]
        label_new_erp = self._multi_epoch_EEG.means_by_labels[label]
        
        self.ERP_Template_Target = self.TemplateRiemann['mu_Epoch_T'][...]
        print self.ERP_Template_Target.shape
        print label_new_erp.shape


        self.CurrCov = self.covariances_EP(label_new_erp, self.ERP_Template_Target)


        scipy.io.savemat('D:\Dycog\Dev_Python\ERP_Template_Target.mat', mdict={'ERP_Template_Target': self.ERP_Template_Target })
        scipy.io.savemat('D:\Dycog\Dev_Python\label_new_erp.mat', mdict={'label_new_erp': label_new_erp })
        scipy.io.savemat('D:\Dycog\Dev_Python\CurrCov.mat', mdict={'CurrCov': self.CurrCov })        
        
         
        MatCov_T = self.TemplateRiemann['mu_MatCov_T'][...]
        MatCov_NT = self.TemplateRiemann['mu_MatCov_NT'][...]
        
        
        scipy.io.savemat('D:\Dycog\Dev_Python\MatCov_T.mat', mdict={'MatCov_T': MatCov_T })        
        scipy.io.savemat('D:\Dycog\Dev_Python\MatCov_NT.mat', mdict={'MatCov_NT': MatCov_NT })        
      
        
        self.Curr_r_TNT = self.predict_R_TNT(self.CurrCov, MatCov_T,MatCov_NT)
        
        scipy.io.savemat('D:\Dycog\Dev_Python\Curr_r_TNT.mat', mdict={'Curr_r_TNT': self.Curr_r_TNT })        
       
        
        mu_rTNT_T  = self.TemplateRiemann['mu_rTNT_T'][...]
        mu_rTNT_NT = self.TemplateRiemann['mu_rTNT_NT'][...]
        sigma_rTNT_T  = self.TemplateRiemann['sigma_rTNT_T'][...]
        sigma_rTNT_NT = self.TemplateRiemann['sigma_rTNT_NT'][...]
        
        
        
        
        
        LikelihoodFunction = self.compute_likelihood(self.Curr_r_TNT, mu_rTNT_T, mu_rTNT_NT,sigma_rTNT_T,sigma_rTNT_NT)
        scipy.io.savemat('D:\Dycog\Dev_Python\LikelihoodFunction.mat', mdict={'LikelihoodFunction': LikelihoodFunction })        

        self.signal_new_LikelihoodFunction_result.emit(LikelihoodFunction)
        self._multi_epoch_EEG.global_reset_trial()



#_______________________________________________________________________________
 



#_______________________________________________________________________________
    def start_watching_signal(self):
        """
        start watching signal before start calib to see which player is P1 and which player is P2
        """
        self._data_acquisition_device.start()
        self.RenameTriggerStream.start()
        self._bandpass_filter.start()

#_______________________________________________________________________________
    def stop_watching_signal(self):
        """
        useful before starting to record data;
        surprinsingly you have to stop/start the data_acquisition_device before saving its streams.
        """
        self._bandpass_filter.stop()
        self.RenameTriggerStream.stop()
        self._data_acquisition_device.stop()




#_______________________________________________________________________________
    def start_online(self):
        """
        make sure the software_triggers_device is started
        """
        
        try:
            self._multi_epoch_EEG.global_reset_trial()

        except (AttributeError, KeyError):
            pass
        self._trial_counter = 0


        self._data_acquisition_device.start()
        self.RenameTriggerStream.start()
#        try:
        self._bandpass_filter.start()
        self._multi_epoch_EEG.start()
#        except AttributeError:
#            pass

#_______________________________________________________________________________
    def stop_online(self):
        """
        make sure to stop the software_triggers_device
        """

#        try:
        self._multi_epoch_EEG.stop()
        self._bandpass_filter.stop()
#        except AttributeError:
#            pass

#        try:
        self.RenameTriggerStream.stop()
        self._data_acquisition_device.stop()
#        except AttributeError:
#            pass

#_______________________________________________________________________________
    def close_all(self):

        try:
            self._multi_epoch_EEG.close()
        except AttributeError:
            pass

        try:
            self.RenameTriggerStream.close()
            self._data_acquisition_device.close()
        except AttributeError:
            pass
                
#_______________________________________________________________________________
    def covariances_EP(self,X, P):
        Ne, Ns = X.shape
        Np, Ns = P.shape

        covmats = np.cov(np.concatenate((X, P), axis=0))
        return covmats
	
#_______________________________________________________________________________
    def predict_R_TNT(self,X, mu_MatCov_T,mu_MatCov_NT):
        """
        Predict the r_TNT for a new set of trials.
        """
        
        dist_0 = self.distance_riemann(X, mu_MatCov_T)
        dist_1 = self.distance_riemann(X, mu_MatCov_NT)
        
#        scipy.io.savemat('D:\MYB\Dev_Python\dist_0.mat', mdict={'dist_0': dist_0 })        
#        scipy.io.savemat('D:\MYB\Dev_Python\dist_1.mat', mdict={'dist_1': dist_1 })        

        
        r_TNT = np.log(dist_0 / dist_1)
        
        return r_TNT
			
	
#_______________________________________________________________________________
    def distance_riemann(self,A, B):
        """Riemannian distance between two covariance matrices A and B.
        .. math::
        d = {\left( \sum_i \log(\lambda_i)^2 \\right)}^{-1/2}
    		
        where :math:`\lambda_i` are the joint eigenvalues of A and B
    		
        :param A: First covariance matrix
        :param B: Second covariance matrix
        :returns: Riemannian distance between A and B
    		
        """
        l_logsquare = np.sum(np.log(eigvalsh(A, B))**2)

        return np.sqrt(l_logsquare)
        
		
		
#_______________________________________________________________________________
    def compute_likelihood(self, l_r_TNT,  l_mu_TNT_T, l_mu_TNT_NT, l_sigma_TNT_T, l_sigma_TNT_NT):
		# 0 is target, 1 is nontarget
		
        Vec0 = (l_r_TNT - l_mu_TNT_T) ** 2
        Vec0 = Vec0 / l_sigma_TNT_T
		
        Vec1 = (l_r_TNT - l_mu_TNT_NT) ** 2
        Vec1 = Vec1 / l_sigma_TNT_NT
		
		
        ld0 = np.log( 2 *np. pi *l_sigma_TNT_T)
        ld1 = np.log(2 * np.pi * l_sigma_TNT_NT)
		
		
        lf0 = - 0.5 * (Vec0 + ld0)
        lf1 = - 0.5 * (Vec1 + ld1)
		

        return np.array([lf0 , lf1])               
