const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

let win;

app.whenReady().then(() => {

    const python = spawn("python", ["launcher.py"]);

    win = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    setTimeout(() => {
        win.loadURL("http://localhost:8501");
    }, 5000);

    win.on("closed", () => {
        python.kill();
    });
});