const { app, BrowserWindow, ipcMain, Menu, dialog } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;
let backendProcess;

// Get the path to python executable or bundled python
function getPythonPath() {
  if (isDev) {
    // In development, use system python
    return 'python';
  } else {
    // In production, look for bundled python
    const bundledPath = path.join(process.resourcesPath, 'python', 'python.exe');
    if (fs.existsSync(bundledPath)) {
      return bundledPath;
    }
    return 'python';
  }
}

// Start Node.js backend server
function startBackendServer() {
  return new Promise((resolve, reject) => {
    // Get backend path - in production it's bundled with the app
    const backendPath = isDev 
      ? path.join(__dirname, '../server')
      : path.join(process.resourcesPath, 'server');

    const indexPath = path.join(backendPath, 'index.js');
    
    console.log('Starting backend server from:', indexPath);
    console.log('Backend path exists:', fs.existsSync(indexPath));

    backendProcess = spawn('node', [indexPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      detached: false,
      cwd: backendPath,
      env: { ...process.env, NODE_ENV: isDev ? 'development' : 'production' }
    });

    let serverStarted = false;

    backendProcess.stdout.on('data', (data) => {
      const message = data.toString();
      console.log(`[Backend] ${message}`);
      if (!serverStarted && (message.includes('listening') || message.includes('3000'))) {
        serverStarted = true;
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data}`);
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend server:', error);
      reject(error);
    });
    
    // Timeout after 15 seconds
    setTimeout(() => {
      if (!serverStarted) {
        console.log('Backend startup timeout - assuming server started');
        resolve();
      }
    }, 15000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      enableRemoteModule: false,
      nodeIntegration: false,
    },
  });

  const startURL = isDev
    ? 'http://localhost:5173'
    : `file://${path.join(__dirname, '../client/dist/index.html')}`;

  mainWindow.loadURL(startURL);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle('open-file-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'All Files', extensions: ['*'] },
      { name: 'CSV Files', extensions: ['csv'] },
      { name: 'Excel Files', extensions: ['xlsx', 'xls'] },
      { name: 'PDF Files', extensions: ['pdf'] },
      ...options?.filters || []
    ],
  });
  return result.filePaths;
});

ipcMain.handle('save-file-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: [
      { name: 'CSV Files', extensions: ['csv'] },
      { name: 'All Files', extensions: ['*'] },
      ...options?.filters || []
    ],
    ...options
  });
  return result.filePath;
});

ipcMain.handle('read-file', async (event, filePath) => {
  return fs.readFileSync(filePath, 'utf-8');
});

ipcMain.handle('write-file', async (event, filePath, content) => {
  fs.writeFileSync(filePath, content, 'utf-8');
  return true;
});

app.on('ready', async () => {
  try {
    console.log('Starting backend server...');
    await startBackendServer();
    console.log('Backend server started');
    
    createWindow();
    
    createMenu();
  } catch (error) {
    console.error('Failed to start application:', error);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  // Cleanup child processes
  if (backendProcess) {
    backendProcess.kill();
  }
  if (pythonProcess) {
    pythonProcess.kill();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Exit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' }
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}
