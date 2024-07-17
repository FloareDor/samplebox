import librosa
import soundfile as sf
import numpy as np
import os
from Tonal_Fragment import Tonal_Fragment
import random
from scipy.stats import skew
from scipy.signal import butter, filtfilt
from wonky_sampler import main as wonky_sampler

def get_key_of_sample(sample, sr):
    tonal_fragment = Tonal_Fragment(sample, sr)
    return tonal_fragment.key.replace(" minor", "m").replace(" major", "")

def load_and_analyze(file_path):
    y, sr = librosa.load(file_path)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    return y, sr, tempo, beat_frames

def extract_drum_hits(drum_stem_path, output_path, amplitude_threshold=0.1, max_samples_per_category=5):
    y, sr = librosa.load(drum_stem_path)
    
    # Compute RMS energy
    rms = librosa.feature.rms(y=y)[0]
    rms_normalized = (rms - np.min(rms)) / (np.max(rms) - np.min(rms))
    
    # Detect onsets
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, wait=1, pre_avg=1, post_avg=1, pre_max=1, post_max=1)
    onset_samples = librosa.frames_to_samples(onset_frames)
    
    def classify_drum_hit(hit):
        # Extract features
        spectral_centroid = librosa.feature.spectral_centroid(y=hit, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=hit, sr=sr)[0]
        zero_crossing_rate = librosa.feature.zero_crossing_rate(hit)[0]
        
        # Simple classification based on spectral and temporal features
        if np.mean(spectral_centroid) < 500 and np.mean(spectral_rolloff) < 2000:
            return "kick"
        elif np.mean(spectral_centroid) > 3000 and np.mean(zero_crossing_rate) > 0.1:
            return "hi_hat"
        elif np.mean(spectral_centroid) > 1000 and np.mean(spectral_centroid) < 3000 and skew(hit) > 0:
            return "snare"
        else:
            return "other"

    def get_low_frequency_amplitude(hit):
        # Design a low-pass Butterworth filter
        nyquist = 0.5 * sr
        cutoff = 200 / nyquist
        b, a = butter(4, cutoff, btype='low', analog=False)
        
        # Apply the filter
        low_freq_hit = filtfilt(b, a, hit)
        return np.max(np.abs(low_freq_hit))

    hits = {"kick": [], "snare": [], "hi_hat": [], "harmonics": []}
    
    for i, start in enumerate(onset_samples):
        start_frame = librosa.samples_to_frames(start)
        if rms_normalized[start_frame] < amplitude_threshold:
            continue
        
        if i < len(onset_samples) - 1:
            end = onset_samples[i+1]
        else:
            end = len(y)
        
        frame_start = librosa.samples_to_frames(start)
        frame_end = librosa.samples_to_frames(end)
        energy_threshold = 0.5 * rms[frame_start]
        
        for frame in range(frame_start, frame_end):
            if rms[frame] < energy_threshold:
                end = librosa.frames_to_samples(frame)
                break
        
        hit = y[start:end]
        
        if len(hit) < int(sr * 0.05):
            end = start + int(sr * 0.05)
            hit = y[start:end]
        
        fade_length = min(int(sr * 0.01), len(hit))
        fade_out = np.linspace(1.0, 0.0, fade_length)
        hit[-fade_length:] *= fade_out
        
        # Classify the drum hit
        drum_type = classify_drum_hit(hit)
        
        # Store hit along with its low frequency amplitude for kicks, regular amplitude for harmonicss
        if drum_type == "kick":
            hits[drum_type].append((hit, get_low_frequency_amplitude(hit)))
        else:
            hits[drum_type].append((hit, np.max(np.abs(hit))))
    
    # Sort and filter hits
    for drum_type in hits:
        if len(hits[drum_type]) > max_samples_per_category:
            hits[drum_type].sort(key=lambda x: x[1], reverse=True)
            hits[drum_type] = hits[drum_type][:max_samples_per_category]
    
    # Save hits for each category
    os.makedirs(output_path, exist_ok=True)
    for drum_type, samples in hits.items():
        for i, (hit, _) in enumerate(samples, 1):
            sf.write(f"{output_path}/{drum_type}_{i}.wav", hit, sr)
    
    print(f"Extracted drum hits to {output_path}:")
    for drum_type, samples in hits.items():
        print(f"  {drum_type}: {len(samples)}")


def extract_harmonic_samples(harmonics_stem_path, output_path, amplitude_threshold=-100, max_samples=18, creative_mode=True):
    y, sr = librosa.load(harmonics_stem_path)
   
    # Estimate tempo and beat frames
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_samples = librosa.frames_to_samples(beat_frames)
   
    # Calculate samples per bar (assuming 4/4 time signature)
    samples_per_bar = 32 * (beat_samples[1] - beat_samples[0])
   
    # Extract one-bar samples
    samples = []
    for i in range(0, len(y) - samples_per_bar, samples_per_bar):
        sample = y[i:i+samples_per_bar]
        sample_rms = np.sqrt(np.mean(sample**2))
        print("sample_rms: ", sample_rms)
        if sample_rms >= amplitude_threshold:
            sample = np.tile(sample, 2)
            samples.append((sample, i/sr, sample_rms))
   
    # Sort samples by RMS amplitude and keep only the top max_samples
    samples.sort(key=lambda x: x[2], reverse=True)
    samples = samples[:max_samples]
   
    # Creative processing function
    def creative_process(sample):
        if np.random.random() < 0.27:  # 35% chance of reverse
            sample = sample[::-1]
        if np.random.random() < 0.35:  # 20% chance of pitch shift
            sample = librosa.effects.pitch_shift(sample, sr=sr, n_steps=np.random.randint(-6, 5))
        if np.random.random() < 0.05:  # 5% chance of time stretch
            sample = librosa.effects.time_stretch(sample, rate=np.random.uniform(0.8, 1.2))
        return sample
   
    # Save samples
    os.makedirs(output_path, exist_ok=True)
    for i, (sample, start_time, _) in enumerate(samples):
        if creative_mode:
            sample = creative_process(sample)
       
        key = get_key_of_sample(sample, sr)
        print("tempo_melodic:", np.around(list(tempo)[0], decimals=0))
        filename = f"{key}.wav"
        sf.write(os.path.join(output_path, filename), sample, sr)
   
    print(f"Extracted {len(samples)} one-bar melodic samples to {output_path}")


def create_percussive_loops_from_original(percs_file, output_dir, num_loops=5, bars_per_loop=2):
    # Load the drum stem
    y, sr = librosa.load(percs_file)
    
    # Estimate tempo and beat frames
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_samples = librosa.frames_to_samples(beat_frames)
    
    # Calculate samples per bar (assuming 4/4 time signature)
    samples_per_bar = 4 * (beat_samples[1] - beat_samples[0])
    
    # Extract bar-length segments
    bar_segments = []
    for i in range(0, len(y) - samples_per_bar, samples_per_bar):
        bar_segments.append(y[i:i+samples_per_bar])
    
    # Create loops
    for i in range(num_loops):
        # Randomly select consecutive bars
        start_bar = random.randint(0, len(bar_segments) - bars_per_loop)
        loop = np.concatenate(bar_segments[start_bar:start_bar + bars_per_loop])
        
        # Apply some subtle variations
        if random.random() < 0.3:
            # Slight tempo variation
            loop = librosa.effects.time_stretch(loop, rate=random.uniform(0.98, 1.02))
        
        if random.random() < 0.2:
            # Subtle pitch variation
            loop = librosa.effects.pitch_shift(loop, sr=sr, n_steps=random.uniform(-0.5, 0.5))
        
        # Normalize the loop
        loop = loop / np.max(np.abs(loop))
        try:
            tempo, _ = librosa.beat.beat_track(y=loop, sr=sr)
            print("tempo:", np.around(list(tempo)[0], decimals=0))
            tempo = np.around(list(tempo)[0], decimals=0)
        except:
            tempo = "unknown"
        # Save the loop
        filename = f"{tempo}_{i}.wav"
        sf.write(os.path.join(output_dir, filename), loop, sr)
    
    print(f"Created {num_loops} drum loops in {output_dir}")

if __name__ == "__main__":
    input_file = "316.mp3"
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)

    filename = input_file.split("/")[-1].replace(".wav", "").replace(".mp3", "")
    results_dir = os.path.join(output_dir, filename)
    os.makedirs(results_dir, exist_ok=True)

    y, sr = librosa.load(input_file)
    song_key = get_key_of_sample(y, sr)
    print(f"song key: {song_key}")
   
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    sf.write(os.path.join(results_dir, "harmonics.wav"), y_harmonic, sr)
    sf.write(os.path.join(results_dir, "percs.wav"), y_percussive, sr)
    # separate_stems(input_file, output_dir)
    print("extracted everything")
    
    # Create drum loops
    drum_hits_dir = os.path.join(results_dir, "drum_hits")
    percussive_loops_dir = os.path.join(results_dir, "percussive_loops")
    os.makedirs(percussive_loops_dir, exist_ok=True)

    percs_file = os.path.join(results_dir, "percs.wav")
    create_percussive_loops_from_original(percs_file, percussive_loops_dir)
    
    # Extract drum hits
    drum_dir = os.path.join(results_dir, "drum_hits")
    os.makedirs(drum_dir, exist_ok=True)
    extract_drum_hits(os.path.join(results_dir, "percs.wav"), drum_dir, amplitude_threshold=0.1)
   
    # Extract melodic samples
    melodic_dir = os.path.join(results_dir, "harmonic_samples")
    os.makedirs(melodic_dir, exist_ok=True)
    extract_harmonic_samples(os.path.join(results_dir, "harmonics.wav"), melodic_dir)
    
    melody_sample = os.path.join(results_dir, "harmonics.wav")
    instrumental_wonky_output_folder = os.path.join(results_dir, "wonky_samples_harmonic")
    
    original_wonky_output_folder = os.path.join(results_dir, "wonky_samples_original")

    wonky_sampler(input_file, original_wonky_output_folder, song_key=song_key)
    wonky_sampler(melody_sample, instrumental_wonky_output_folder, song_key=song_key)