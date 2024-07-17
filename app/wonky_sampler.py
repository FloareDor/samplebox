import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from Tonal_Fragment import Tonal_Fragment
import random
import os

def get_bpm_and_bars(file_path, song_key=None):
    y, sr = librosa.load(file_path)
    if song_key == None:
        song_key = get_key_of_bar(y, sr)
    print('get_key_of_bar(y, sr):', song_key)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    
    # assuming 4/4 time signature
    bar_duration = 60 / tempo  # in seconds
    
    bar_duration = bar_duration
    
    total_duration = librosa.get_duration(y=y, sr=sr)
    num_bars = int(total_duration // bar_duration)
    
    bars = []
    for i in range(num_bars):
        start = int(i * bar_duration * sr)
        end = int((i + 1) * bar_duration * sr)
        bars.append(y[start:end])
    
    return tempo, bars, sr, song_key

def get_key_of_bar(bar, sr):
    tonal_fragment = Tonal_Fragment(bar, sr)
    key = tonal_fragment.key
    if 'minor' in key:
        return key.replace(' minor', 'm')
    else:
        return key.replace(' major', '')

def get_chord_progression(song_key):
    chord_numerals = []
    if 'm' == song_key[-1]:
        print("minor key:", song_key)
        chord_numerals = random.choice(minor_chord_progressions)
    else:
        chord_numerals = random.choice(major_chord_progressions)
    print(chord_numerals)
    chord_progression = [chord_chart[song_key][i-1] for i in chord_numerals]
    
    return [chord_progression]

chord_chart = {
  'A': ['A', 'Bm', 'C#m', 'D', 'E', 'F#m', 'G#'],
  'A#': ['A#', 'Cm', 'Dm', 'D#', 'F', 'Gm', 'A'],
  'B': ['B', 'C#m', 'D#m', 'E', 'F#', 'G#m', 'A#'],
  'C': ['C', 'Dm', 'Em', 'F', 'G', 'Am', 'B'],
  'C#': ['C#', 'D#', 'Fm', 'F#', 'G#', 'A#m', 'C'],
  'D': ['D','Em', 'F#m', 'G', 'A', 'Bm', 'C#'],
  'D#': ['D#', 'Fm', 'Gm', 'G#', 'A#', 'Cm', 'D'],
  'E': ['E','F#m', 'G#m', 'A', 'B', 'C#m', 'D#'],
  'F': ['F','Gm', 'Am', 'A#', 'C', 'Dm', 'E'],
  'F#': ['F#', 'G#m', 'A#m', 'C', 'D', 'D#m', 'F'],
  'G': ['G','Am', 'Bm', 'C', 'D', 'Em', 'F#'],
  'G#': ['G#', 'A#m', 'Cm', 'C#', 'D#', 'Fm', 'G'],

  "Cm": ["Cm", "Ddim", "D#", "Fm", "Gm", "G#", "A#"],
  "C#m": ["C#m", "D#dim", "E", "F#m", "G#m", "A", "B"],
  "Dm": ["Dm", "Edim", "F", "Gm", "Am", "A#", "C"],
  "D#m": ["D#m", "Edim", "F#", "G#m", "A#m", "B", "C#"],
  "Em": ["Em", "F#dim", "G", "Am", "Bm", "C", "D"],
  "Fm": ["Fm", "Gdim", "G#", "A#m", "Cm", "C#", "D#"],
  "F#m": ["F#m", "G#dim", "A", "Bm", "C#m", "D", "E"],
  "Gm": ["Gm", "Adim", "A#", "Cm", "Dm", "D#", "F"],
  "G#m": ["G#m", "A#dim", "B", "C#m", "D#m", "E", "F#"],
  "Am": ["Am", "Bdim", "C", "Dm", "Em", "F", "G"],
  "A#m": ["A#m", "Cdim", "C#", "D#m", "Fm", "F#", "G#"],
  "Bm": ["Bm", "C#dim", "D", "Em", "F#m", "G", "A"]
}

major_chord_progressions = [
    [1, 4, 6, 5],
    [1,4,1,5],
    [1,5,4,5],
    [1,5,6,4],
    [1,4,5,4],
    [1,6,4,5],
    [1,5,6,3,4,1,4,5],
]

minor_chord_progressions = [
    [1, 4, 5, 1],
    [1,6,3,7],
    [1,6,7,5],
    [1,3,4,4],
    [1,5,3,3]
    
]

chord_progressions = [
    [1, 4, 6, 5],
    [1, 4, 5, 1]
    # [1, 5, 6, 4],
    # [6, 4, 1, 5],
    # [1, 1, 1, 1, 4, 4, 1, 1, 5, 4, 1, 1],
    # [1,6,4,5],
    # [1, 7, 6, 5],
    # [1, 5, 6, 3, 4, 1, 4, 5],
    # [4, 5, 3, 6]
]

def transpose_bar(bar, sr, from_key, to_key):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    from_note = from_key.replace('m', '')
    to_note = to_key.replace('m', '')
    
    # Ensure we're transposing between the same key types (major to major, minor to minor)
    if from_key.endswith('m') != to_key.endswith('m'):
        return bar  # Return original bar if key types don't match
    
    semitones = (notes.index(to_note) - notes.index(from_note)) % 12
    return librosa.effects.pitch_shift(bar, sr=sr, n_steps=semitones)

def create_new_song_segment(bars, sr, song_key):
    new_song = []
    
    progression = get_chord_progression(song_key=song_key)[0]
    # print("progression:", progression, type(progression))
    for chord in progression:
        # print(chord, type(chord))
        # Find a bar that matches the chord
        matching_bars = [bar for bar, key in bars if key == chord]
        if matching_bars:
            chosen_bar = random.choice(matching_bars)
        else:
            # If no matching bar, take a random bar with matching key type and transpose it
            matching_key_type_bars = [
                (bar, key) for bar, key in bars
                if key.endswith('m') == chord.endswith('m')
            ]
            if matching_key_type_bars:
                random_bar, random_key = random.choice(matching_key_type_bars)
                chosen_bar = transpose_bar(random_bar, sr, random_key, chord)
            else:
                # If no matching key type, just use a random bar without transposing
                chosen_bar, _ = random.choice(bars)
        if np.random.random() < 0.3:
            chosen_bar = librosa.effects.time_stretch(chosen_bar, rate=random.choice([0.5,1]))
        chosen_bar = creative_process(chosen_bar, sr)
        new_song.append(chosen_bar)
    return np.concatenate(new_song), progression[0]

def creative_process(sample, sr):
    if np.random.random() < 0.35:  # 30% chance of reverse
        sample = sample[::-1]
    return sample

def creative_process2(sample, sr):
    if np.random.random() < 0.25:  # 30% chance of reverse
        sample = sample[::-1]
    if np.random.random() < 0.5:  # 20% chance of pitch shift
        sample = librosa.effects.pitch_shift(sample, sr=sr, n_steps=np.random.randint(-8, 5))
    if np.random.random() < 0.1:  # 10% chance of time stretch
        sample = librosa.effects.time_stretch(sample, rate=np.random.uniform(0.8, 1.2))
    return sample

def create_full_song(bars, sr, output_folder, song_key):

    for i in range(4):
        segment, _ = create_new_song_segment(bars, sr, song_key=song_key)
        segment = np.tile(segment, 4)
        segment = creative_process2(segment, sr)
        tempo = "unknown"
        try:
            tempo, _ = librosa.beat.beat_track(y=segment, sr=sr)
            # print("tempo:", np.around(list(tempo)[0], decimals=0))
            tempo = np.int32(list(tempo)[0])
        except:
            continue
        key = get_key_of_bar(segment,sr)
        sf.write(output_folder + f"/{tempo}_{str(key).replace("#","-sharp")}_{i}.wav".replace("sharpm", "sharp-m"), segment, sr)

def main(input_file, output_folder, song_key=None, instrumental=False):

    tempo, bar_audio, sr, song_key = get_bpm_and_bars(input_file, song_key=song_key)
    # print(f'Estimated BPM: {tempo}')
    
    # Get the key for each bar
    bars_with_keys = [(bar, get_key_of_bar(bar, sr)) for bar in bar_audio]
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Create and save the new song
    create_full_song(bars_with_keys, sr, output_folder, song_key)
    print(f'New song saved as {output_folder}')

if __name__ == '__main__':
    input_file = 'more.mp3'
    output_folder = '3333'

    main(input_file, output_folder, song_key='D#m')