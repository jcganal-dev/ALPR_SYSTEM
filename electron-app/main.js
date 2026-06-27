process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
});
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const treeKill = require('tree-kill');
const http = require('http');

let mainWindow;
let serverProcess;
let splashWindow;

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 550,
    height: 350,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    center: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
}

function createWindow() {
  createSplashWindow();

  mainWindow = new BrowserWindow({
    fullscreen: true,       // Starts in true fullscreen
    frame: true,            // Removes the top title bar/buttons
    autoHideMenuBar: true,   // Keeps the Alt-key menu hidden
    show: false,            // HIDDEN initially while splash is visible
    icon: path.join(__dirname, 'assets/icon.ico'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false // Common requirement for older nodeIntegration scripts
    },
    title: "LPR System"
  });

  // --- THE FIX: PREVENT NEW WINDOWS (Ctrl+Click) ---
  mainWindow.webContents.setWindowOpenHandler(() => {
    return { action: 'deny' };
  });

  const isPackaged = app.isPackaged;
  const baseDir = isPackaged 
    ? path.join(process.resourcesPath, '../../../..')
    : path.join(__dirname, '..');

  console.log('Starting Python server in:', baseDir);

  serverProcess = spawn('uvicorn', ['main:app', '--host', '127.0.0.1', '--port', '8000', '--log-level', 'warning'], {
    cwd: baseDir,
    shell: true,
    stdio: 'ignore'
  });

  let loaded = false;
  const checkServer = () => {
    if (loaded) return;
    const req = http.get('http://127.0.0.1:8000/', (res) => {
      // Server responded!
      loaded = true;
      mainWindow.loadURL('http://127.0.0.1:8000/');
      
      // Once the URL starts loading, show the window
      mainWindow.once('ready-to-show', () => {
        if (splashWindow) splashWindow.close(); // Close splash when main is ready
        mainWindow.show();
        mainWindow.focus();
      });
    });

    req.on('error', () => {
      setTimeout(checkServer, 500);
    });
  };

  checkServer();

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

// --- APP LIFECYCLE ---
app.on('ready', createWindow);

app.on('window-all-closed', function () {
  if (serverProcess && serverProcess.pid) {
    // Kill the Python server before quitting
    treeKill(serverProcess.pid, 'SIGTERM', (err) => {
      app.quit();
    });
  } else {
    app.quit();
  }
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});
