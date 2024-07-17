const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const https = require('node:https')

let fs = require('fs').promises;
const AdmZip = require('adm-zip');
const jetpack = require('fs-jetpack');

function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            // "Content-Security-Policy": [ "default-src 'self'" ]
        }
    });

    win.loadFile('src/index.html');
    return win;
}

fs = require('fs');
const iconName = path.join(__dirname, 'iconForDragAndDrop.png');
const icon = fs.createWriteStream(iconName);
fs = require('fs').promises;
https.get('https://img.icons8.com/ios/452/drag-and-drop.png', (response) => {
  response.pipe(icon)
})

let mainWindow;

app.whenReady().then(() => {
    mainWindow = createWindow();
});

ipcMain.handle('get-save-path', async () => {
    const defaultDir = app.getPath('appData');
    return defaultDir;
});

ipcMain.on('ondragstart', (event, filePath) => {
    event.sender.startDrag({
        file: filePath,
        icon: iconName  // Make sure you have this icon file in your project
    });
});


ipcMain.handle('save-and-extract-samplebox', async (event, arrayBuffer) => {
    try {
        const buffer = Buffer.from(arrayBuffer);
        let baseSaveDir = app.getPath('appData');
        let saveDir = path.join(baseSaveDir, 'samplebox');
        await jetpack.dirAsync(saveDir);
        
        let savePath = path.join(saveDir, 'sample_box.zip');
        await fs.writeFile(savePath, buffer);

        const zip = new AdmZip(savePath);
        const extractPath = path.dirname(savePath);

        zip.extractAllTo(extractPath, true);
        await fs.unlink(savePath);

        return { success: true, extractPath };
    } catch (error) {
        console.error('Error in save-and-extract-samplebox:', error);
        return { success: false, error: "save-and-extract-samplebox: "+error.message };
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});


async function scanDirectory(dir) {
    let results = {};
    const items = await fs.readdir(dir, { withFileTypes: true });
    
    for (const item of items) {
        if (item.isDirectory()) {
            const subDir = path.join(dir, item.name);
            // Check if this is a UUID directory
            const subItems = await fs.readdir(subDir, { withFileTypes: true });
            if (subItems.length === 1 && subItems[0].isDirectory()) {
                // This is likely the UUID directory, go one level deeper
                const songDir = path.join(subDir, subItems[0].name);
                results[item.name] = {
                    songName: subItems[0].name,
                    samples: await scanDirectory(songDir)
                };
            } else {
                results[item.name] = await scanDirectory(subDir);
            }
        } else if (item.isFile() && ['.mp3', '.wav'].includes(path.extname(item.name).toLowerCase())) {
            const parentDir = path.basename(dir);
            if (!results[parentDir]) {
                results[parentDir] = [];
            }
            results[parentDir].push(item.name);
        }
    }
    
    return results;
}

ipcMain.handle('get-audio-path', async (event, uuid, songName, category, filename) => {
    const name = filename.replace("#", "%23");
    const baseSaveDir = app.getPath('appData');
    const sampleboxDir = path.join(baseSaveDir, 'samplebox');
    const categoryParts = category.split('/');
    const filePath = path.join(sampleboxDir, uuid, songName, ...categoryParts, name);
    const fileExtension = path.extname(filename).slice(1);
    return { path: `file://${filePath}`, extension: fileExtension };
});


ipcMain.handle('scan-samples', async (event, extractPath) => {
    try {
        const samples = await scanDirectory(extractPath);
        return { success: true, samples };
    } catch (error) {
        console.error('Error scanning samples:', error);
        return { success: false, error: "scan-samples: "+ error.message };
    }
});

ipcMain.handle('scan-all-samples', async () => {
    const baseSaveDir = app.getPath('appData');
    const sampleboxDir = path.join(baseSaveDir, 'samplebox');
    return await scanDirectory(sampleboxDir);
});


ipcMain.on('navigate', (event, page) => {
    if (mainWindow) {
        mainWindow.loadFile(`${page}`);
    } else {
        console.error('mainWindow is not defined');
    }
});

ipcMain.handle('delete-sample', async (event, filePath) => {
    try {
        await fs.unlink(filePath);
        return { success: true };
    } catch (error) {
        console.error('Error deleting sample:', error);
        return { success: false, error: error.message };
    }
});

// ipcMain.handle('get-audio-path', async (event, category, filename) => {
//     const baseSaveDir = app.getPath('appData');
//     const sampleboxDir = path.join(baseSaveDir, 'samplebox');
//     const categoryParts = category.split('/');
//     const filePath = path.join(sampleboxDir, ...categoryParts, filename);
//     const fileExtension = path.extname(filename).slice(1);
//     return { path: `file://${filePath}`, extension: fileExtension };
// });