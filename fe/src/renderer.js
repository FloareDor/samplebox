let isGenerating = false;
let ws;
let pendingFile = null;

function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        return Promise.resolve(); // WebSocket is already connected
    }

    return new Promise((resolve, reject) => {
        ws = new WebSocket('ws://localhost:8000/ws');

        ws.onopen = () => {
            console.log('WebSocket connection established');
            resolve();
        };

        ws.onmessage = async (event) => {
            if (event.data instanceof Blob) {
                // This is the zip file
                const arrayBuffer = await event.data.arrayBuffer();
                const result = await window.electron.saveAndExtractSamplebox(arrayBuffer);

                if (result.success) {
                    document.getElementById('result').innerHTML = `
                    <p class="text-green-400">Sample box generated and extracted successfully!</p>
                    <p class="text-sm text-gray-400">Samples saved to: ${result.extractPath}</p>
                `;
                    console.log('Samples saved to:', result.extractPath);

                    // Delay navigation to show the success message
                    setTimeout(() => {
                        window.electron.navigateTo('src/browser.html');
                    }, 2000);
                } else {
                    throw new Error(result.error);
                }
            } else {
                // This is a status message
                console.log(event.data);
                const data = JSON.parse(event.data);
                document.getElementById('result').innerHTML = `
                <p class="text-yellow-400">${data.message}</p>
            `;
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            document.getElementById('result').innerHTML = `
            <p class="text-red-400">WebSocket error: ${error.message}</p>
        `;
            reject(error);
        };

        ws.onclose = () => {
            console.log('WebSocket connection closed');
            isGenerating = false;
            updateBrowseButton();
        };
    });
}

// Function to handle file upload
async function handleFileUpload(file) {
    if (!file) {
        alert('Please select a song file');
        return;
    }

    try {
        // Show loading state
        isGenerating = true;
        document.getElementById('result').innerHTML = `
            <p class="text-yellow-400">Connecting to server... Please wait.</p>
        `;
        updateBrowseButton();

        // Connect WebSocket before sending the file
        await connectWebSocket();

        document.getElementById('result').innerHTML = `
            <p class="text-yellow-400">Generating sample box... Please wait.</p>
        `;

        const reader = new FileReader();
        reader.onload = function(e) {
            const arrayBuffer = e.target.result;
            if (ws.readyState === WebSocket.OPEN) {
                // Create a new ArrayBuffer with filename and file data
                const filenameBuffer = new TextEncoder().encode(file.name);
                const combinedBuffer = new ArrayBuffer(4 + filenameBuffer.byteLength + arrayBuffer.byteLength);
                const combinedView = new DataView(combinedBuffer);

                // Write filename length (4 bytes)
                combinedView.setUint32(0, filenameBuffer.byteLength);

                // Write filename
                new Uint8Array(combinedBuffer).set(filenameBuffer, 4);

                // Write file data
                new Uint8Array(combinedBuffer).set(new Uint8Array(arrayBuffer), 4 + filenameBuffer.byteLength);

                ws.send(combinedBuffer);
            } else {
                console.error('WebSocket is not open. ReadyState:', ws.readyState);
                document.getElementById('result').innerHTML = `
                    <p class="text-red-400">Error: WebSocket is not open. Please try again.</p>
                `;
            }
        };
        reader.readAsArrayBuffer(file);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('result').innerHTML = `
            <p class="text-red-400">Error: ${error.message}</p>
        `;
        isGenerating = false;
        updateBrowseButton();
    }
}
// Trigger file input when the Upload button is clicked
document.getElementById('generateBtn').addEventListener('click', () => {
    document.getElementById('songInput').click();
});

// Handle file selection
document.getElementById('songInput').addEventListener('change', (event) => {
    const file = event.target.files[0];
    handleFileUpload(file);
});

// Drag and drop functionality
const dropZone = document.getElementById('generateBtn');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('bg-gray-700'); // Visual feedback
});

dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('bg-gray-700');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('bg-gray-700');
    
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
});

function displaySamples(samples) {
    const sampleList = document.getElementById('sampleList');
    sampleList.innerHTML = '';

    async function renderCategory(uuid, songName, category, files, level = 0) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'mb-4 ml-' + (level * 4);
        categoryDiv.innerHTML = `<h3 class="text-xl font-bold mb-2">${category}</h3>`;

        const fileList = document.createElement('ul');
        fileList.className = 'list-disc pl-5';

        for (const [key, value] of Object.entries(files)) {
            if (Array.isArray(value)) {
                // This is a list of audio files
                for (const file of value) {
                    const listItem = document.createElement('li');
                    listItem.className = 'mb-2';
                    
                    // Use the correct category path here
                    const audioCategory = level === 0 ? key : category;
                    const { path: audioPath, extension } = await window.electron.getAudioPath(uuid, songName, audioCategory, file);
                    
                    listItem.innerHTML = `
                        <p>${file}</p>
                        <audio controls>
                            <source src="${audioPath}" type="audio/${extension}">
                            Your browser does not support the audio element.
                        </audio>
                    `;

                    // Make the list item draggable
                    listItem.draggable = true;
                    listItem.addEventListener('dragstart', (event) => {
                        event.preventDefault();
                        window.electron.startDrag(audioPath.replace('file://', ''));
                    });

                    fileList.appendChild(listItem);
                }
            } else {
                // This is a subcategory
                const subCategory = level === 0 ? key : `${category}/${key}`;
                const subCategoryDiv = await renderCategory(uuid, songName, subCategory, value, level + 1);
                fileList.appendChild(subCategoryDiv);
            }
        }

        categoryDiv.appendChild(fileList);
        return categoryDiv;
    }

    try {
        (async () => {
            for (const [uuid, contents] of Object.entries(samples)) {
                const songName = contents.songName;
                const topCategoryDiv = await renderCategory(uuid, songName, songName, contents.samples, 0);
                sampleList.appendChild(topCategoryDiv);
            }
        })();
    } catch (e) {
        console.log("error: " + e.message);
    }
}

function updateBrowseButton() {
    const browseButton = document.getElementById('browseSamplesBtn');
    browseButton.disabled = isGenerating;
    browseButton.classList.toggle('opacity-50', isGenerating);
    browseButton.classList.toggle('cursor-not-allowed', isGenerating);
}

document.getElementById('browseSamplesBtn').addEventListener('click', () => {
    if (!isGenerating) {
        window.electron.navigateTo('src/browser.html');
    }
});

updateBrowseButton();