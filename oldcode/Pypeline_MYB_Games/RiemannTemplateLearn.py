import numpy as np
import sys

import scipy.io 
sys.path.append('..\..\python_crnl_bci\PyLyonBci')
from pyriemann.utils.mean import mean_riemann

import pylyonbci
from pylyonbci import pyrte

from pylyonbci.CustomTermcolor import *
#from pylyonbci import pyrte

#import matplotlib.pyplot as plt

#import ipdb

import os
import datetime

import pyqtgraph as pg

#===============================================================================
def debug():
    from PyQt4.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()
    from ipdb import set_trace
    set_trace()
#===============================================================================


def RiemannTemplateLearn(file_complete_path,  analysis_time_window_sec=1, threshold_rejection=0.1):

    #ouvre un fichier .vhrd (brainproducts)
    nom_de_code_du_sujet = file_complete_path.split('/')[-1].split('.vhdr')[0]
    nom_de_code_du_sujet = nom_de_code_du_sujet.split('-')[0] #si on choisi le fichier manuellement il faut supprimer la date dans le nom de fichier
    
    modif_date = pyrte.utils.get_modification_date(file_complete_path)
    custom_print_in_green('opening file *** ', file_complete_path.split('/')[-1], 'modified on', modif_date)
    
    
    
    custom_print_in_blue('reading vhdr file')
    data = pyrte.utils.read_brainampfile(file_complete_path)    
    
    
    data['eventarray_indexes'] = np.rint(data['eventarray_indexes']) #etre certain de ne pas avoir d'erreur d'arrondi
    data['eventarray_indexes'] = data['eventarray_indexes'] - 1
    
    
    
    
    data['analog_signals'] = pyrte.algorithms.preprocessing_bandpassfilter(
                                                                    signal_channels=data['analog_signals'], 
                                                                    sampling_rate=data['sampling_rate'], 
                                                                    filter_order=2, 
                                                                    low_freq_cutoff=.5, 
                                                                    hi_freq_cutoff=20)
                                                                    
    #    scipy.io.savemat('C:\_MANU\_U821\Stage\Raphaelle\POS.mat', mdict={'POS': data['eventarray_indexes'] })
    #    scipy.io.savemat('C:\_MANU\_U821\Stage\Raphaelle\DataPy.mat',mdict={'DataPy': data['analog_signals']})
    
    calib_target_sequence = [[7,4,2,6,3,1,5,1,4,3,7,6,2,5,2,5,7,1,6,3,4]]
    
    
    
    sampling_frequency = data['sampling_rate']
    
    
    Offset = 0 #ms
    Offset = np.fix(Offset * sampling_frequency/ 1000 )    
    custom_print_in_yellow('Offset',Offset)    
    number_of_channels, samples_per_channels = data['analog_signals'].shape
    nb_samples_analysis_time_window = (int)(analysis_time_window_sec * sampling_frequency)
    custom_print_in_yellow('nb_samples_analysis_time_window',nb_samples_analysis_time_window)
    nombre_colonnes = 7
    number_of_events = data['eventarray_indexes'].shape[0]
    
    nombre_repetitions = number_of_events/(nombre_colonnes*21)
    
    #    custom_print_in_blue('index',data['eventarray_indexes'])
    
    data['eventarray_indexes'] = data['eventarray_indexes'] + Offset#ici
    events_positions = np.column_stack((data['eventarray_indexes'], data['eventarray_labels']))
    pos_events_P300_mask = (data['eventarray_labels'] > 0) & (data['eventarray_labels'] < 8)
    events_positions = events_positions[pos_events_P300_mask] #Suppression of non-events P300 stimulations
    custom_print_in_yellow('P300 stimulations number =', events_positions.shape[0])

    #verifier si assez de triggers dans le fichier de donnees et comparer avec la sequence de target du stimulateur
    if events_positions.shape[0] != (len(calib_target_sequence[0]) * nombre_repetitions * nombre_colonnes):
        #np.unique(events_positions[:, 1]) # to see the event code labels
        raise Exception('data do not match parameters: needs {} trials but found {} trials in saved data'.format(len(calib_target_sequence[0]), events_positions.shape[0]/(nombre_repetitions * nombre_colonnes)))
    else:
        custom_print_in_blue('***', file_complete_path.split('/')[-1], 'contains', events_positions.shape[0] / (nombre_repetitions * nombre_colonnes), 'targets with', nombre_repetitions, 'flashes')

    #event_code_target: (event_code_indexes, event_code_labels, bool_target)
    event_code_target = list()
    for index_target, target in enumerate(calib_target_sequence[0]):
        flashes_sequence_per_target = range(
                                        index_target*nombre_repetitions*nombre_colonnes,
                                        (index_target+1)*nombre_repetitions*nombre_colonnes)
        try:
            event_code_target.append(np.column_stack((events_positions[flashes_sequence_per_target], events_positions[flashes_sequence_per_target, 1] == target)))
        except IndexError:
            custom_print_in_red('not enough data to process parameters')
    event_code_target = np.array(event_code_target)
    event_code_target = event_code_target.reshape((event_code_target.shape[0]*event_code_target.shape[1], event_code_target.shape[2]))

    
    epochs_all_data_channels = pyrte.algorithms.rte_Epoching(data['analog_signals'], event_code_target[:, 0], nb_samples_analysis_time_window)
    #custom_print_in_blue('epochs_all_data_channels',epochs_all_data_channels[0,0, 0:200])    # chan *trials * sample                                                       
    #scipy.io.savemat('\\10.69.111.22\dycog\Jeremie\MindYourBrain\Dev\epoch1.mat', mdict={'Epoch1': epochs_all_data_channels[0,0, :]})
    #scipy.io.savemat('D:\Dycog\Dev_Python\epoch1.mat', mdict={'Epoch1': epochs_all_data_channels[0,0, :]})
#    scipy.io.savemat('C:\_MANU\_U821\Stage\Raphaelle\event_code_target.mat', mdict={'event_code_target': event_code_target[:, 0] })
#    scipy.io.savemat('C:\_MANU\_U821\Stage\Raphaelle\epoch1.mat', mdict={'Epoch1': epochs_all_data_channels[0,0, :]})
    scipy.io.savemat('D:\Dycog\wip\epochs_all_data_channels.mat', mdict={'epochs_all_data_channels': epochs_all_data_channels})
    
#    epochs_maxvalue = epochs_all_data_channels.max(2).max(0)
    absepochs_maxvalue = np.fabs(epochs_all_data_channels)
    epochs_maxvalue = absepochs_maxvalue.max(2).max(0)

    if (threshold_rejection>0):
        reject_above_threshold = np.sort(epochs_maxvalue)[np.fix(epochs_maxvalue.size*(1-threshold_rejection)).astype(np.int)]
        epochs_to_remove_indexes = np.where(epochs_maxvalue > reject_above_threshold)[0]
        event_code_target_with_threshold_rejection = np.delete(event_code_target, epochs_to_remove_indexes, axis=0)
        custom_print_in_yellow('applying', epochs_to_remove_indexes.size, 'threshold rejections over', reject_above_threshold, 'uV')

    else:
        epochs_to_remove_indexes = []
        event_code_target_with_threshold_rejection = event_code_target
    
	
    epochs_data_channels_clean = pyrte.algorithms.rte_Epoching(data['analog_signals'], event_code_target_with_threshold_rejection[:, 0], nb_samples_analysis_time_window)
    Epochs_T = []
    Epochs_NT = []
  
  
    for i in range(epochs_data_channels_clean.shape[1]):
        epoch = epochs_data_channels_clean[:,i,:]
        if event_code_target_with_threshold_rejection[i,2] == 1:
            Epochs_T.append(epoch)
        else:
            Epochs_NT.append(epoch)
  
        	
	
 
    Epochs_T = np.array(Epochs_T)
    Epochs_NT = np.array(Epochs_NT)


    		
    ERP_Template_Target = np.mean(Epochs_T, axis = 0)
    ERP_Template_NoTarget = np.mean(Epochs_NT, axis = 0)
	
    VarERP_Template_Target = np.var(Epochs_T, axis = 0)
    VarERP_Template_NoTarget = np.var(Epochs_NT, axis = 0)
    
    
    MatCov_TrialTarget = pyrte.utils.matCov(Epochs_T, ERP_Template_Target)
    MatCov_TrialNoTarget = pyrte.utils.matCov(Epochs_NT, ERP_Template_Target)
    

    MatCov_TrialTarget=np.array(MatCov_TrialTarget)
    MatCov_TrialNoTarget=np.array(MatCov_TrialNoTarget)
    
    scipy.io.savemat('D:\Dycog\wip\MatCov_TrialTarget.mat', mdict={'MatCov_TrialTarget': MatCov_TrialTarget})
    scipy.io.savemat('D:\Dycog\wip\MatCov_TrialNoTarget.mat', mdict={'MatCov_TrialNoTarget': MatCov_TrialNoTarget})
    
    mean_MatCov_Target = mean_riemann(MatCov_TrialTarget)
    mean_MatCov_NoTarget = mean_riemann(MatCov_TrialNoTarget)
    scipy.io.savemat('D:\Dycog\wip\mean_MatCov_Target.mat', mdict={'mean_MatCov_Target': mean_MatCov_Target})
    scipy.io.savemat('D:\Dycog\wip\mean_MatCov_NoTarget.mat', mdict={'mean_MatCov_NoTarget': mean_MatCov_NoTarget})
    Mu_rTNT_TrialTarget,  Var_rTNT_TtrialTarget, All_rTNT_TrialTarget   = pyrte.utils.compute_rTNT(MatCov_TrialTarget,mean_MatCov_Target,mean_MatCov_NoTarget)
    Mu_rTNT_TrialNoTarget,Var_rTNT_TrialNoTarget,All_rTNT_TrialNoTarget = pyrte.utils.compute_rTNT(MatCov_TrialNoTarget,mean_MatCov_Target,mean_MatCov_NoTarget)
    NbGoodTarget = float(np.sum(All_rTNT_TrialTarget < .0))
    NbGoodNoTarget = float(np.sum(All_rTNT_TrialNoTarget > .0))
    NbTotTrials = float(All_rTNT_TrialTarget.shape[0]+All_rTNT_TrialNoTarget.shape[0])  
    AccP300 =  np.float64((NbGoodTarget+NbGoodNoTarget)*100 /NbTotTrials)
    
    TemplateRiemann = {}
    TemplateRiemann['mu_Epoch_T'] = ERP_Template_Target
    TemplateRiemann['mu_Epoch_NT'] = ERP_Template_NoTarget
    TemplateRiemann['var_Epoch_T'] = VarERP_Template_Target
    TemplateRiemann['var_Epoch_NT'] = VarERP_Template_NoTarget	
    TemplateRiemann['mu_MatCov_T'] = mean_MatCov_Target
    TemplateRiemann['mu_MatCov_NT'] = mean_MatCov_NoTarget
    TemplateRiemann['mu_rTNT_T'] = Mu_rTNT_TrialTarget
    TemplateRiemann['mu_rTNT_NT'] = Mu_rTNT_TrialNoTarget
    TemplateRiemann['sigma_rTNT_T'] = Var_rTNT_TtrialTarget      
    TemplateRiemann['sigma_rTNT_NT'] = Var_rTNT_TrialNoTarget      
    TemplateRiemann['AccP300'] = AccP300

    return (TemplateRiemann)
	

########################### MAIN PROGRAM #######################################
def _mean_var_plot(pyqtgraph_plot_item, mean, variance, pencolor=(255, 255, 255), brushcolor=(255, 255, 255, 100)):
    #        pyqtgraph_plot_item.clear()
            mean_plot = pyqtgraph_plot_item.plot(mean, pen=pencolor, antialias=True)
            mean_variance_plot1 = pyqtgraph_plot_item.plot(mean + np.sqrt(variance), pen=brushcolor)
            mean_variance_plot2 = pyqtgraph_plot_item.plot(mean - np.sqrt(variance), pen=brushcolor)
            mean_variance_plot1.curve.path = mean_variance_plot1.curve.generatePath(*mean_variance_plot1.curve.getData())
            mean_variance_plot2.curve.path = mean_variance_plot2.curve.generatePath(*mean_variance_plot2.curve.getData())
            mean_variance_fill = pg.FillBetweenItem(mean_variance_plot1, mean_variance_plot2, brush=brushcolor)
            pyqtgraph_plot_item.addItem(mean_variance_fill)

#_______________________________________________________________________________

def one_player_learn(directory, filename):
    (score_LOO_crossvalidation, 
    NB_parameters_for_n_spatial_filters, 
    W_xdawn, 
    optimal_nb_of_spatial_filter) = C4_learn(os.path.join(directory, filename), nb_repetitions=4, analysis_time_window_sec=0.875,threshold_rejection=0.1)

    nb_of_spatial_filter = 0 #premier filtre spatial
    target_mean_player1 = NB_parameters_for_n_spatial_filters[nb_of_spatial_filter]['m2']
    target_variance_player1 = NB_parameters_for_n_spatial_filters[nb_of_spatial_filter]['v2']
    not_target_mean_player1 = NB_parameters_for_n_spatial_filters[nb_of_spatial_filter]['m1']
    not_target_variance_player1 = NB_parameters_for_n_spatial_filters[nb_of_spatial_filter]['v1']

    p1 = pg.plot(title='{} LOO CrossValidation: {}%'.format(filename, score_LOO_crossvalidation))
    _mean_var_plot(p1.plotItem, not_target_mean_player1, not_target_variance_player1)
    _mean_var_plot(p1.plotItem, target_mean_player1, target_variance_player1, pencolor=(255, 255, 0), brushcolor=(255, 255, 0, 100))
    return p1
    
    
    

if __name__ == '__main__':

    directory_raw = '/home/coffee/_BciApps/Connect4_PyAcq/raw_data'
    filename_raw = 'BOURO2015_03_09_13_01Raw'
    one_player_learn(directory_raw, filename_raw)













