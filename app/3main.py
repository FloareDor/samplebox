import os
import zipfile
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time

import librosa
import soundfile as sf
import numpy as np
from Tonal_Fragment import Tonal_Fragment
from wonky_sampler import main as wonky_sampler

# Import custom modules
from perc_splitter import process_song, extract_drum_hits, extract_harmonic_samples, get_key_of_sample, create_percussive_loops_from_original
from wonky_sampler import main as wonky_sampler

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_bytes()

            # Extract filename length (first 4 bytes)
            filename_length = int.from_bytes(data[:4], byteorder='big')

            # Extract filename
            filename = data[4:4+filename_length].decode('utf-8')
            filename = str(filename).replace(".mp3", "").replace(".wav", "")

            # Extract file data
            file_data = data[4+filename_length:]

            async def send_message(message):
                await websocket.send_text(json.dumps(message))
            
            # Generate a unique UUID for this upload
            upload_uuid = str(uuid.uuid4())
            
            # Create the results directory
            results_dir1 = os.path.join("results", upload_uuid)
            results_dir = os.path.join(results_dir1, upload_uuid)
            os.makedirs(results_dir, exist_ok=True)

            os.makedirs(f"{results_dir}/{filename}/stems")
            
            # Save the uploaded file
            input_file_path = os.path.join(f"{results_dir}/{filename}/stems", f"{filename}.wav")
            with open(input_file_path, "wb") as buffer:
                buffer.write(file_data)
            
            # Send progress update
            await send_message({"status": "processing", "message": "File received and saved"})

            # Process the song and generate samples
            # await process_song(input_file_path, results_dir, send_message)
            input_file = input_file_path
            output_dir = results_dir
            # Create results directory
            filename = os.path.basename(input_file).replace(".wav", "").replace(".mp3", "")
            results_dir = os.path.join(output_dir, filename)
            os.makedirs(results_dir, exist_ok=True)

            # Load the audio file
            y, sr = librosa.load(input_file)
            
            # Get the song key
            song_key = get_key_of_sample(y, sr)
            print(f"Song key: {song_key}")
            await asyncio.sleep(0.5)
            await send_message({"status": "processing", "message": "Extracting stems ..."})

            # Separate harmonic and percussive components
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            stems_dir = os.path.join(results_dir, "stems")
            os.makedirs(stems_dir, exist_ok=True)

            sf.write(os.path.join(stems_dir, "harmonics.wav"), y_harmonic, sr)
            sf.write(os.path.join(stems_dir, "percs.wav"), y_percussive, sr)
            print("Extracted harmonic and percussive components")
            await asyncio.sleep(0.5)
            await send_message({"status": "processing", "message": "Creating percussion loops ..."})
            # Create drum loops
            percussive_loops_dir = os.path.join(results_dir, "percussions")
            os.makedirs(percussive_loops_dir, exist_ok=True)

            percs_file = os.path.join(stems_dir, "percs.wav")
            create_percussive_loops_from_original(percs_file, percussive_loops_dir)
            await asyncio.sleep(0.5)
            await send_message({"status": "processing", "message": "Extracting drum hits ..."})
            # Extract drum hits
            drum_dir = os.path.join(results_dir, "drums")
            os.makedirs(drum_dir, exist_ok=True)
            extract_drum_hits(os.path.join(stems_dir, "percs.wav"), drum_dir, amplitude_threshold=0.1)
            await asyncio.sleep(0.5)
            await send_message({"status": "processing", "message": "Getting harmonic loops ..."})
            # Extract melodic samples
            melodic_dir = os.path.join(results_dir, "harmonic stuff")
            os.makedirs(melodic_dir, exist_ok=True)
            extract_harmonic_samples(os.path.join(stems_dir, "harmonics.wav"), melodic_dir)
            await asyncio.sleep(0.5)
            await send_message({"status": "processing", "message": "Generating wonky loops from original audio ..."})
            # Generate wonky samples
            melody_sample = os.path.join(stems_dir, "harmonics.wav")
            instrumental_wonky_output_folder = os.path.join(results_dir, "wonky stuff")
            original_wonky_output_folder = os.path.join(results_dir, "wonky stuff")

            wonky_sampler(input_file, original_wonky_output_folder, song_key=song_key)
            await asyncio.sleep(0.5)
            await send_message({"status": "processing", "message": "Generating wonky loops from harmonics ... (this gon take a min)"})
            wonky_sampler(melody_sample, instrumental_wonky_output_folder, song_key=song_key)

            print(f"Processed song and generated samples in {results_dir}")
            
            # Send progress update
            await websocket.send_text(json.dumps({"status": "processing", "message": "Samples generated"}))
            time.sleep(5)
            # Create a zip file containing all generated samples
            zip_path = os.path.join(results_dir, f"{upload_uuid}_samplebox.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, _, files in os.walk(results_dir1):
                    for file in files:
                        if file.endswith('.zip'):
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, results_dir1)
                        zipf.write(file_path, arcname)
            
            # Send the zip file
            with open(zip_path, "rb") as zip_file:
                zip_data = zip_file.read()
                await websocket.send_bytes(zip_data)
            
            # Send completion message
            await websocket.send_text(json.dumps({"status": "complete", "message": "Sample box generated and sent"}))
            
            time.sleep(5)
            
            # Cleanup
            shutil.rmtree(results_dir1)
            
        except Exception as e:
            await websocket.send_text(json.dumps({"status": "error", "message": str(e)}))
            break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)