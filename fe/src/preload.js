const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
    startDrag: (filePath) => ipcRenderer.send('ondragstart', filePath),
    saveDialog: () => ipcRenderer.invoke('save-dialog'),
    saveAndExtractSamplebox: (arrayBuffer) => ipcRenderer.invoke('save-and-extract-samplebox', arrayBuffer),
    scanSamples: (extractPath) => ipcRenderer.invoke('scan-samples', extractPath),
    getAudioPath: (uuid, songName, category, filename) => ipcRenderer.invoke('get-audio-path', uuid, songName, category, filename),
    
    scanAllSamples: () => ipcRenderer.invoke('scan-all-samples'),
    navigateTo: (page) => ipcRenderer.send('navigate', page),

    deleteSample: (filePath) => ipcRenderer.invoke('delete-sample', filePath),
});