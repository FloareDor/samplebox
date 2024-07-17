let fullSamples = {}; // Store the full samples data

document.addEventListener('DOMContentLoaded', async () => {
    fullSamples = await window.electron.scanAllSamples();
    displaySongList(fullSamples);
});

document.getElementById('backBtn').addEventListener('click', () => {
    window.electron.navigateTo('src/index.html');
});

function displaySongList(samples) {
    const songList = document.getElementById('songList');
    songList.innerHTML = '';

    // Add some CSS to the page for the blob styling
    const style = document.createElement('style');
    style.textContent = `
        .song-blob {
            width: 130px;
            height: 130px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            margin: 20px;
			filter: blur(1px);
        }
        .song-blob:hover {
            transform: scale(1.05);
			width: 180px;
            height: 180px;
			filter: blur(0px);
        }
        .song-blob::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-size: cover;
            background-position: center;
            filter: blur(50px);
            z-index: 1;
        }
        .song-blob h3 {
            position: relative;
            z-index: 2;
            color: white;
            text-align: center;
            padding: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
    `;
    document.head.appendChild(style);

    // Create a container for flex layout
    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.flexWrap = 'wrap';
    container.style.justifyContent = 'center';

    for (const [uuid, contents] of Object.entries(samples)) {
        const songName = contents.songName;
        const songDiv = document.createElement('div');
        songDiv.className = 'song-blob';

        // Generate random number for image
        const randomNumber = Math.floor(Math.random() * (160 - 134 + 1)) + 134;
        const imagePath = `../img/images/seeds/seed0${randomNumber}.png`;

        // Set background image
        songDiv.style.setProperty('--bg-image', `url('${imagePath}')`);
        songDiv.style.backgroundImage = `var(--bg-image)`;

        songDiv.innerHTML = `<h3 class="text-xl font-semibold">${songName.length > 4 ? songName.slice(0, 4) : songName}</h3>`;
        songDiv.addEventListener('click', () => displayCategories(uuid, songName, contents.samples));
        container.appendChild(songDiv);
    }

    songList.appendChild(container);
}

function displayCategories(uuid, songName, samples) {
    document.getElementById('songList').classList.add('hidden');
    document.getElementById('categoryView').classList.remove('hidden');
    document.getElementById('selectedSong').textContent = songName;

    const categoryList = document.getElementById('categoryList');
    categoryList.innerHTML = '';

    // Add CSS for category blobs
    const style = document.createElement('style');
    style.textContent = `
        .category-container {
            position: relative;
            width: 100%;
            height: 60vh;
            margin-bottom: 20px;
        }
        .category-blob {
            position: absolute;
            width: 150px;
            height: 150px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            overflow: hidden;
            filter: blur(1px);
        }
        .category-blob:hover {
            transform: scale(1.1);
            filter: blur(0px);
			width: 175px;
            height: 175px;
			z-index:1000;
        }
        .category-blob::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-size: cover;
            background-position: center;
            filter: blur(50px);
            z-index: 1;
        }
        .category-blob span {
            position: relative;
            z-index: 2;
            color: white;
            text-align: center;
            padding: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            font-weight: bold;
        }
    `;
    document.head.appendChild(style);

    const categoryContainer = document.createElement('div');
    categoryContainer.className = 'category-container';
    categoryList.appendChild(categoryContainer);

    const categories = Object.keys(samples);

    // Define positions for each blob
    const positions = [
        { top: '5%', left: '5%' },     // Top left
        { top: '5%', right: '5%' },    // Top right
        { bottom: '5%', left: '5%' },  // Bottom left
        { bottom: '5%', right: '5%' }, // Bottom right
        { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' } // Center
    ];

    categories.forEach((category, index) => {
        if (index >= positions.length) return; // Skip if we run out of predefined positions

        const categoryBlob = document.createElement('div');
        categoryBlob.className = 'category-blob';

        // Generate random number for image
        const randomNumber = Math.floor(Math.random() * (160 - 134 + 1)) + 134;
        const imagePath = `../img/images/seeds/seed0${randomNumber}.png`;

        // Set background image
        categoryBlob.style.setProperty('--bg-image', `url('${imagePath}')`);
        categoryBlob.style.backgroundImage = `var(--bg-image)`;

        const textSpan = document.createElement('span');
        textSpan.textContent = category;
        categoryBlob.appendChild(textSpan);

        // Apply the position
        Object.assign(categoryBlob.style, positions[index]);

        categoryBlob.addEventListener('click', () => displaySamples(uuid, songName, category, samples[category]));
        categoryContainer.appendChild(categoryBlob);
    });

    // Add an empty div for the sample rendering
    const sampleRenderingArea = document.createElement('div');
    sampleRenderingArea.id = 'sampleRenderingArea';
    categoryList.appendChild(sampleRenderingArea);
}

let wavesurfers = []; // Array to store all WaveSurfer instances

async function displaySamples(uuid, songName, category, files) {
    const sampleRenderingArea = document.getElementById('sampleRenderingArea');
    sampleRenderingArea.innerHTML = '';
    wavesurfers = []; // Reset the wavesurfers array

    const renderFile = async (file) => {
        const { path: audioPath, extension } = await window.electron.getAudioPath(uuid, songName, category, file);
        
        const sampleDiv = document.createElement('div');
        sampleDiv.className = 'mb-8 relative';

        const headerDiv = document.createElement('div');
        headerDiv.className = 'flex justify-between items-center mb-2';
        sampleDiv.appendChild(headerDiv);

        const nameDiv = document.createElement('div');
        nameDiv.className = 'text-lg font-semibold';
        nameDiv.textContent = file;
        headerDiv.appendChild(nameDiv);

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn text-gray-400 hover:text-red-500 transition-colors duration-200 z-10';
        deleteBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
        `;
        deleteBtn.addEventListener('click', async (event) => {
            event.stopPropagation();
            const result = await window.electron.deleteSample(audioPath.replace('file://', '').replace("#", "%23"));
            if (result.success) {
                sampleDiv.remove();
            } else {
                alert(`Failed to delete sample: ${result.error}`);
            }
        });
        headerDiv.appendChild(deleteBtn);

        const waveformDiv = document.createElement('div');
        waveformDiv.className = 'waveform-container';
        sampleDiv.appendChild(waveformDiv);

        const wavesurfer = WaveSurfer.create({
            container: waveformDiv,
            waveColor: '#7AABC1',
            progressColor: '#4F8FA3',
            url: audioPath.replace("#", "%23"),
            interact: true,
            height: 100,
        });

        wavesurfers.push(wavesurfer); // Add this WaveSurfer instance to the array

        wavesurfer.on('play', () => {
            // Pause all other WaveSurfer instances
            wavesurfers.forEach(ws => {
                if (ws !== wavesurfer && ws.isPlaying()) {
                    ws.pause();
                }
            });
        });

        wavesurfer.on('interaction', () => {
            wavesurfer.playPause();
        });

        sampleDiv.draggable = true;
        sampleDiv.addEventListener('dragstart', (event) => {
            event.preventDefault();
            window.electron.startDrag(audioPath.replace('file://', '').replace("#", "%23"));
        });

        sampleRenderingArea.appendChild(sampleDiv);
    };

    if (Array.isArray(files)) {
        for (const file of files) {
            await renderFile(file);
        }
    } else if (typeof files === 'object') {
        for (const [subCategory, subFiles] of Object.entries(files)) {
            const subCategoryDiv = document.createElement('div');
            subCategoryDiv.className = 'mb-6';
            subCategoryDiv.innerHTML = `<h3 class="text-xl font-semibold mb-2">${subCategory}</h3>`;
            sampleRenderingArea.appendChild(subCategoryDiv);

            if (Array.isArray(subFiles)) {
                for (const file of subFiles) {
                    await renderFile(file);
                }
            } else {
                console.error('Unexpected file structure:', subFiles);
            }
        }
    } else {
        console.error('Unexpected files structure:', files);
    }
}