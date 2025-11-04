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

def apploadfile(path=None, map_path=None):
    time_start_overall = time.time()
    dir_name = ('./data/')
    #path = askdirectory(initialdir=dir_name, title="Select directory where data are stored")
    path = '.\data\rec_250604_135546_161646'

    run_first_time = True
    map_path = './data/map_linear.csv' 

    time_start = time.time()


    # Configure loading
    load_raw= True # vs filtered
    load_from_file=True  # True: pre-saved file vs multiple rhs
    downsample = 1 # Chronic recordings from VN sampled at 20KHz    

    # Start and dur in samples (multiply by freq if needed)
    start_min= 0 #80                   
    dur_min= 40# 1-0   #0 = whole recording                 
    port = 'Port B' #

    # with open("%s/day.txt"%path, "r") as f:
    #     day = f.read()
    day = 'Day4'
    print(port)

    #For E1 and E2 fs = 30000
    # Rest fs = 20000
    fs = 20000
    start=fs*60*start_min   #CHANGE FS!!!
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

if __name__ == "__main__":
    rec = apploadfile()