import os
import zipfile
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import time

# Import custom modules
from perc_splitter import process_song
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

def cleanup(path: str):
    """Remove files and directories."""
    time.sleep(10)
    # if os.path.isdir(path):
    #     shutil.rmtree(path)
    # elif os.path.isfile(path):
    #     os.remove(path)

@app.post("/generate-samplebox")
async def generate_samplebox(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Generate a unique UUID for this upload
    upload_uuid = str(uuid.uuid4())
    
    # Create the results directory
    results_dir1 = os.path.join("results", upload_uuid)
    results_dir = os.path.join(results_dir1, upload_uuid)
    os.makedirs(results_dir, exist_ok=True)

    filename = file.filename.replace(".wav", "").replace(".mp3", "")
    os.makedirs(f"{results_dir}/{filename}/stems")
    
    # Save the uploaded file
    input_file_path = os.path.join(f"{results_dir}/{filename}/stems", file.filename)
    with open(input_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process the song and generate samples
    process_song(input_file_path, results_dir)
    
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
    
    # Schedule cleanup tasks
    background_tasks.add_task(cleanup, results_dir)
    
    # Return the zip file
    return FileResponse(zip_path, media_type="application/zip", filename=f"{upload_uuid}_samplebox.zip")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)