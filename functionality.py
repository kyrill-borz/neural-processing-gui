import IPython
import os
import sys
import json
import time
import datetime
import pycwt
import statistics
import random
import pickle
import polars as pl 
#import h5py
import numpy as np
import scipy as sp
import pandas as pd
import seaborn as sns
#import sklearn as sk
import tkinter as tk
import matplotlib.pyplot as plt
from sklearn import metrics
from sklearn import decomposition
from sklearn.decomposition import PCA
from tkinter import *
from tkinter import ttk
from sklearn import preprocessing
from datetime import date
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
from scipy import signal as sg


# from neurodsp.rhythm import sliding_window_matching
# from neurodsp.utils.download import load_ndsp_data
# from neurodsp.plts.rhythm import plot_swm_pattern
# from neurodsp.plts.time_series import plot_time_series
# from neurodsp.utils import set_random_seed, create_times
# Import listed chormap
from matplotlib.colors import ListedColormap
import matplotlib.dates as md
from matplotlib import colors as mcolors
# Scipy
from scipy import signal
from scipy import ndimage
# TKinter for selecting files
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askdirectory
from scipy.stats import zscore


# Add my module to python path
sys.path.append("../")

# Own libraries
from utils.load_data import load_setup, load_matfiles, load_data_multich, load_bsamples
from utils.utils import *
from utils.Neurogram import * 

os.environ['KMP_DUPLICATE_LIB_OK']='True'


## configs

time_start_overall = time.time()
dir_name = './data/'
# path = askdirectory(initialdir=dir_name, title="Select directory where data are stored")
path = './data/rec_250604_135546_161646'

run_first_time = True
map_path = './data/map_linear.csv' 

time_start = time.time()

# Configuration
load_raw = True  # vs filtered
load_from_file = True  # True: pre-saved file vs multiple rhs
downsample = 1  # Chronic recordings from VN sampled at 20KHz    

# Start and duration in samples (multiply by freq if needed)
start_min = 20
dur_min = 5
port = 'Port B'

# Example hardcoded for now
day = 'Day4'
print(port)

fs = 20000
start = fs * 60 * start_min
dur = None if dur_min == 0 else fs * 60 * dur_min

options_filter = [
    "None", 
    "butter", 
    "fir"]                # Binomial Weighted Average Filter

options_detection = [
    "get_spikes_threshCrossing", # Ojo: get_spikes_threshCrossing needs detects also cardiac 
                                     # spikes, so use cardiac_window. This method is slower
    "get_spikes_method",         # Python implemented get_spikes() method. Faster
    "so_cfar"]                    # Smallest of constant false-alarm rate filter

options_threshold = [
    "positive",
    "negative", 
    "both_thresh"]

filt_config = {
    'W': [300, 600], #[300, 2000], #[4950], #   [50] lowpass for HR,  [400, 8000], 4950 if fs is 10000 (needs to be <fs/2 per Nyquist)
    'None': {},
    'Automatic': {},  # Will be determined by the adaptive filter function
    'Butterworth': {
            'N': 4,                # The order of the filter
            'btype': 'bandpass', #'bandpass', #'hp'  #'lowpass'     # The type of filter.
            'fs': 20000,
    },
    'Lowpass': {
            'N': 4,                # The order of the filter
            'Wn' : 50,
            'fs': 20000,
            'btype': 'lowpass', #'bandpass', #'hp'  #'lowpass'     # The type of filter.
    },
    'butter_non_causal': {   # Not valid for real time applications
        'N': 4,                # The order of the filter
        'btype': 'bandpass', #'bandpass', #'hp'  #'lowpass'     # The type of filter.
    },
    'fir': {
            'n': 4,
    },
    'notch': {
            'quality_factor': 30,
    },
}

#filt_config['butter']['fs'] = record.fs

# config_text = ['Load_from_file %s' %load_from_file, 'Filter: %s'%record.apply_filter, 'Detection: %s'%record.detect_method, 'Threhold type: %s'%record.thresh_type, 'Channels: %s' %record.channels, 'Downsampling: %s' %downsample]
# config_text.append('Port %s' %(port))
# config_text.append('Start %s, Dur: %s' %(start,dur))
# config_text.append('Channels: %s' %record.channels)
# config_text.append('filt_config: %s' %json.dumps(filt_config))

def apploadfile(path=None, map_path=None):

    if dur_min == 0:
        dur= None 
    else: 
        dur = fs*60*dur_min       
        
    if load_raw:
        # Load original raw pkl/parquet
        record = Recording.open_record(path, start=start, dur=dur, 
                                    load_from_file=load_from_file, 
                                    load_multiple_files=True,
                                    downsample=downsample,
                                    port=port  ,  # Select recording port
                                    map_path=map_path,
                                    day=day,
                                    verbose=0)
    else:
        # Load filtered pkl
        filepath = askopenfile(initialdir=path, title="Select previously stored data file", 
                                    filetypes=(   [("Pickle Files", "*.pkl"), 
                                                ("Parquet Files", "*.parquet"),
                                                ("All Files", "*.*")]))  # Add more file types if needed
        try:
            record = pd.read_pickle(filepath.name)
        except: 
            record = pd.read_parquet(filepath.name) # 
        print(record.recording)
        record.recording.name = 'HF_filtered' # Change name

    record.channels = 'all' #'5, 24, 26, 27, 28' # # OldFFC:     NewFFC: 5, 20, 24, 26, 27, 28

    print("Time elapsed in loading: {} seconds".format(time.time()-time_start)) 
    return record

def apploadfilepolars(start_min, dur_min, path=None, map_path=None):
    print("functionality.py")
    fs = 20000
    start = fs * 60 * start_min
    dur = None if dur_min == 0 else fs * 60 * dur_min
    if load_raw:
        # Load using your custom Recording class
        record = Recording.open_record(
            path,
            start=start,
            dur=dur,
            load_multiple_files=False,
            downsample=downsample,
            port=port,
            map_path=map_path,
            day=day,
            verbose=0
        )
    else:
        # Load filtered data using Polars
        filepath = askopenfile(
            initialdir=path,
            title="Select previously stored data file",
            filetypes=[
                ("Pickle Files", "*.pkl"),
                ("Parquet Files", "*.parquet"),
                ("RHS Files", "*.rhs"),
                ("All Files", "*.*")
            ]
        )

        if filepath.name.endswith('.parquet'):
            record = pl.read_parquet(filepath.name)
        elif filepath.name.endswith('.pkl'):
            # Polars doesn’t directly read pickle files, so fall back to pandas temporarily
            import pandas as pd
            record = pl.from_pandas(pd.read_pickle(filepath.name))
        else:
            record = pl.read_csv(filepath.name)  # fallback for csv-like

        print("Loaded file:", filepath.name)
        # If record has nested structure like record.recording, adapt accordingly
        if hasattr(record, "recording"):
            record.recording.name = 'HF_filtered'

    record.channels = 'all'
    print(f"Time elapsed in loading: {time.time() - time_start:.2f} seconds")

    return record

def displayinformation(record, port, start, dur, downsample, load_from_file, path):
    record.channels = [24,25,26,27,28,29,30,31] #E9, E10, E11

    # Configure
    group = 'HR'
    config_text = []
    record.apply_filter = options_filter[1]    
    record.detect_method = options_detection[2]                                    
    record.thresh_type = options_threshold[0]

    record.path = path  
    config_text = ['Load_from_file %s' %load_from_file, 'Filter: %s'%record.apply_filter, 'Detection: %s'%record.detect_method, 'Threhold type: %s'%record.thresh_type, 'Channels: %s' %record.channels, 'Downsampling: %s' %downsample]
    config_text.append('Port %s' %(port))
    config_text.append('Start %s, Dur: %s' %(start,dur))
    config_text.append('Channels: %s' %record.channels)
    config_text.append('filt_config: %s' %json.dumps(filt_config))

    print('SELECTED GENERAL CONFIGURATION:')
    print('Filter: %s'%record.apply_filter)
    print('Detection: %s'%record.detect_method)
    print('Threhold type: %s'%record.thresh_type)
    print('Channels: %s' %record.channels)   # Intan channels (0-31)
    print('-------------------------------------')

    record.select_channels(record.channels) # keep_ch_loc=True if we want to display following the map. Otherwise follow the order provided by selected channels.
    print('map_array: %s' %record.map_array)     #1D array with the corresponding intan channels (0-31) for linear electrode device (1-32 electrodes): map_array[0] is intan channel corresponding to electrode 1
    print('ch_loc: %s' %record.ch_loc)           #[list of int] list with electrodes locations corresponding to the selected intan channels (inverse of map_array: ch_loc[0] is electrode corresponding to intan ch0 )
    print('filter_ch %s' %record.filter_ch)      #[list of string] list with the selected intan channels in string mode (starting in 'ch_')
    print('Z_magnitude %s' %record.Z_magnitude)  # Impedance of selected intan channels

def plotraw(record):
    # Plot raw data
    cmap = 'gist_ncar' # 'nipy_spectral'
    load_raw = True
    colorbar_ticks_raw=[0, -50]
    plot_ch=record.channels[0]
    if load_raw:
        '''
        record.plot_signal(record.recording.loc[record.recording.index[int(0*60*record.fs)]:record.recording.index[int(0*60*record.fs)] + pd.Timedelta(seconds=(20*60))],
                        plot_ch, record.num_rows,record.num_columns, record.channels,
                        text_label='raw', text_title='Raw signal: intan channel',ylim=[-200, 200],figsize=(10, 10), no_label=False, 
                        dtformat='%M:%S', savefigpath='%s/figures/%s_%s_original-%s.svg' %(record.path, port, group, current_time),
                        show_plot=True)

        '''
        record.plot_freq_content(record.original,int(plot_ch), nperseg=512, max_freq=5000, ylim=[-500,500], dtformat='%H:%M:%S',
                                figsize=(10, 10), 
                                show=True,  cmap=cmap, colorbar_ticks=colorbar_ticks_raw) 
def apply_butterworth_filter(df, sos, channels):
                # Create a copy of the DataFrame to avoid modifying the original data
                df_filtered = df.copy()

                # Initialize filter state with sosfilt_zi
                zi = sg.sosfilt_zi(sos)

                # Apply the filter and update NaN values inside the loop
                for channel in channels:
                    mask_nan = df_filtered[channel].isna()
                    df_filtered[channel], zi = sg.sosfilt(sos, df_filtered[channel].fillna(0.0), zi=zi)
                    df_filtered[channel][mask_nan] = np.nan
                    nan_counts = df_filtered[channel].isna().sum()
                    #print("Number of NaN values in each column:")
                    #print(nan_counts)

                return df_filtered

def plotfiltered(record, plot=True):
    if load_raw:
        time_start = time.time()

        # If applied clean_df and have Nan values (clean then filter)
        if record.recording.name == 'clean':
            kargs = filt_config[record.apply_filter]
            kargs['fs'] = record.fs
            sos = sg.butter(**kargs, output='sos')  # Coefficients for SOS filter

            # Apply the Butterworth filter to the specified channels
            record.filtered = apply_butterworth_filter(record.recording, sos, record.filter_ch)
        else:
            signal2filter = record.original ###record.original #record.recording
            #config_text.append('signal2filter: %s' %signal2filter.name)
            record.filter(signal2filter, record.apply_filter, **filt_config[record.apply_filter])
            # Change from float64 to float 16
            record.filtered = convertDfType(record.filtered, typeFloat=pl.Float32)
            #print(record.filtered.dtypes)
        print("Time elapsed: {} seconds".format(time.time()-time_start))
        record.recording=record.filtered
        record.recording.name = 'filtered'

        nperseg=512
        no_label = False
        cmap = 'gist_ncar' # 'nipy_spectral'
        text_label = 'Filtered'
        plot_ch=record.channels[0]
        text = 'Channels after %s filtering'%record.apply_filter
        
        if filt_config['Butterworth']['btype'] == 'lowpass':
            freq_max = filt_config['W'][0]
            textf = 'LF'
            colorbar_ticks_filt=[20,0,-20,-40]
        else:
            freq_max = filt_config['W'][1] #2000 #chronic: 4000
            textf = 'HF'
            colorbar_ticks_filt= [5, 0, -50, -100, -150, -200] # in vivo: [5, 0, -50, -100, -150, -200]#, -250] #[-10, -35]  ex vivo: [-50, -100]
        
        #'''
        start_time = record.filtered["time"][0] \
            + datetime.timedelta(seconds=float((start_min - start_min) * 60))

        # End time (10 minutes later)
        end_time = start_time + datetime.timedelta(seconds=10 * 60)

        # Filter Polars DataFrame by datetime column
        df_window = record.filtered.filter(
            (pl.col("time") >= start_time) & (pl.col("time") <= end_time)
        )
        num_rows = len(record.filtered)
        num_columns = 1
        # record.plot_signal(
        #     df_window,
        #     plot_ch, num_rows, num_columns,
        #     channels=record.channels, text_label=text_label,
        #     text_title='Butter signal: intan _channel',
        #     ylim=[-100,100], figsize=(20, 10),
        #     no_label=no_label, savefigpath='', show_plot=True
        # )
        if plot:
            record.plot_freq_content(
                record.filtered,
                int(plot_ch), nperseg=nperseg,
                max_freq=freq_max, ylim=[-200, 50],
                dtformat='%H:%M:%S', figsize=(10, 10),
                show=True, cmap=cmap,
                colorbar_ticks=colorbar_ticks_filt
            )

def referencing(record, ref_ch_name='median', plot=True):
    signal = record.filtered # original

    if ref_ch_name == 'median':
        print(ref_ch_name)
        #all_ch_list = [col for col in record.original.columns if col.startswith('ch_')]
        all_ch_list = record.filter_ch # [col for col in record.filter_ch if col.startswith('ch_')] # record.filter_ch ['ch_4', 'ch_11', 'ch_20', 'ch_21']
        ref_ch = signal.select(
            pl.concat_list(all_ch_list).list.median().alias("ref_median")
        )
        print (ref_ch)
        references_df = signal.with_columns(
            [
                pl.col(col) - ref_ch["ref_median"]
                for col in record.filter_ch
            ]
        )
                
    elif ref_ch_name == 'mean':
            print(ref_ch_name)
            #all_ch_list = [col for col in record.original.columns if col.startswith('ch_')]
            all_ch_list = record.filter_ch# [col for col in record.filter_ch if col.startswith('ch_')] # record.filter_ch ['ch_4', 'ch_11', 'ch_20', 'ch_21']
            ref_ch = signal.select(
                pl.concat_list(all_ch_list).list.mean().alias("ref_mean")
            )
            print (ref_ch)
            references_df = signal.with_columns(
                [
                    pl.col(col) - ref_ch["ref_mean"]
                    for col in record.filter_ch
                ]
            )
                
    elif ref_ch_name == 'weighted_laplacian':
        wrong_order = record.channels  # The available channels
        correct_order = [13, 12, 19, 20, 21, 22, 11, 10]  # Full intended order

        # Find the available channels in the correct order
        available_channels = [ch for ch in correct_order if ch in wrong_order]
        channel_indices = {ch: i for i, ch in enumerate(correct_order)}  # Map channel to position
        print("Available channels:", available_channels)

        # Step 2: Apply Weighted Laplacian referencing using all available channels
        laplacian_references = []

        for ch in available_channels:
            print(f'Processing channel {ch}...')
            ch_name = f'ch_{ch}'  # Ensure column names are in the format 'ch_22'
            
            # Find the index of the current channel in correct_order
            current_index = correct_order.index(ch)
            
            # Identify all other available channels and their distances
            neighbors = []
            distances = []
            
            for neighbor in available_channels:
                if neighbor != ch:  # Avoid self-referencing
                    neighbors.append(f'ch_{neighbor}')
                    distances.append(abs(current_index - correct_order.index(neighbor)))  # Compute spatial distance
            
            # Compute weights: Closer neighbors get higher weights
            distances = np.array(distances)
            weights = 1 / distances  # Inverse of distance
            weights /= weights.sum()  # Normalize so sum(weights) = 1
            
            # Compute weighted reference
            neighbors_data = signal[neighbors]
            weighted_ref = (neighbors_data * weights).sum(axis=1)
            
            # Apply Laplacian referencing (subtract weighted reference from current channel)
            laplacian_references.append(signal[ch_name] - weighted_ref)

            # Step 3: Assemble the final DataFrame
            laplacian_df = pd.DataFrame(np.array(laplacian_references).T, columns=[f'ch_{ch}' for ch in available_channels])

            # Step 4: Keep the same datetime index as the original signal DataFrame
            laplacian_df.index = signal.index

            # Step 5: Store the Weighted Laplacian-referenced signals
            references_df = laplacian_df

            # Display the first few rows (optional)
            print(references_df.head())
    if plot:
            print("Plotting referenced data...")
            nperseg=512
            no_label = False
            plot_ch=record.channels[0]
            cmap = 'gist_ncar' # 'nipy_spectral
            colorbar_ticks_filt=[20,0,-20,-40]
            record.plot_freq_content(
                references_df,
                int(plot_ch), nperseg=nperseg,
                max_freq=5000, ylim=[-200, 50],
                dtformat='%H:%M:%S', figsize=(10, 10),
                show=True, cmap=cmap,
                colorbar_ticks=colorbar_ticks_filt
            )


if __name__ == "__main__":
    rec = apploadfilepolars()
    displayinformation(rec, port, start, dur, downsample, load_from_file, path)
    signal2filter = rec.original ###record.original #record.recording
    rec.apply_filter = 'Lowpass'
    #config_text.append('signal2filter: %s' %signal2filter.name)
    rec.filter(signal2filter, rec.apply_filter, channels=rec.filter_ch, **filt_config[rec.apply_filter])
    referencing(rec)