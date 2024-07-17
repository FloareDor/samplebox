from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import tempfile
import uuid
import librosa
from Tonal_Fragment import Tonal_Fragment
from wonky_sampler import main as wonky_sampler
import time

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
RESULTS_DIR = "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def cleanup_dirs(upload_dir: str, results_dir: str):
    time.sleep(2)
    shutil.rmtree(upload_dir, ignore_errors=True)
    shutil.rmtree(results_dir, ignore_errors=True)

@app.post("/sample")
async def create_wonky_samples(background_tasks: BackgroundTasks, file: UploadFile = File(...) ):
    # Generate UUID for this process
    process_id = str(uuid.uuid4())
    
    # Create directories
    upload_dir = os.path.join(UPLOAD_DIR, process_id)
    results_dir = os.path.join(RESULTS_DIR, process_id)
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    # Save uploaded file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Determine song key
        y, sr = librosa.load(file_path)
        tonal_fragment = Tonal_Fragment(y, sr)
        song_key = tonal_fragment.key.replace(" minor", "m").replace(" major", "")
        
        # Create wonky samples
        wonky_output_folder = os.path.join(results_dir, "wonky_samples")
        os.makedirs(wonky_output_folder, exist_ok=True)
        wonky_sampler(file_path, wonky_output_folder, song_key=song_key)
        
        # Prepare results
        wonky_samples = os.listdir(wonky_output_folder)
        
        # Create a zip file of the results
        zip_path = os.path.join(results_dir, "wonky_samples.zip")
        shutil.make_archive(zip_path[:-4], 'zip', wonky_output_folder)
        
        background_tasks.add_task(cleanup_dirs, upload_dir, results_dir)
        
        return FileResponse(zip_path, filename="wonky_samples.zip")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)