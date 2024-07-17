import librosa
import soundfile as sf
import numpy as np
import os
from Tonal_Fragment import Tonal_Fragment
import random
from scipy.stats import skew
from scipy.signal import butter, filtfilt
from wonky_sampler import main as wonky_sampler

input_file = "Veera_F8000_Bin4_Weight-Q_075_VGood.mp3"

# Load the audio file
y, sr = librosa.load(input_file)

# Separate harmonic and percussive components
y_harmonic, y_percussive = librosa.effects.hpss(y)
sf.write(os.path.join("", "harmonics.wav"), y_harmonic, sr)
sf.write(os.path.join("", "percs.wav"), y_percussive, sr)