const { app, BrowserWindow, dialog, shell } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const net = require("node:net");
const path = require("node:path");

const HOST = "127.0.0.1";
const PORT = 48193;
const APP_URL = `http://${HOST}:${PORT}`;
const STARTUP_TIMEOUT_MS = 30000;
const STARTUP_RETRY_MS = 250;

let backendProcess;
let backendLog;
let mainWindow;
let shutdownRequested = false;
let backendExit;
let backendReady = false;

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    await startBackend();
    await createMainWindow();
  }).catch((error) => {
    dialog.showErrorBox(
      "LibScope could not start",
      `${error.message}\n\nBackend logs: ${path.join(app.getPath("userData"), "backend.log")}`,
    );
    app.quit();
  });

  app.on("activate", () => {
    if (mainWindow === null && !backendExit) {
      createMainWindow().catch((error) => {
        dialog.showErrorBox("LibScope could not open", error.message);
      });
    }
  });

  app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
  });

  app.on("before-quit", (event) => {
    if (backendProcess && backendProcess.exitCode === null && !shutdownRequested) {
      event.preventDefault();
      shutdownRequested = true;
      backendProcess.once("exit", () => app.quit());
      backendProcess.kill("SIGTERM");
      const forceStop = setTimeout(() => {
        if (backendProcess && backendProcess.exitCode === null) backendProcess.kill("SIGKILL");
      }, 3000);
      forceStop.unref();
    }
  });
}

async function assertPortAvailable() {
  const server = net.createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(PORT, HOST, () => {
      server.close((error) => error ? reject(error) : resolve());
    });
  });
}

function getBackendCommand(dataDirectory) {
  const environment = {
    ...process.env,
    LIBSCOPE_API_KEY: "",
    LIBSCOPE_CORS_ORIGINS: APP_URL,
    LIBSCOPE_DEBUG: "false",
    LIBSCOPE_DESKTOP_DATA_DIR: dataDirectory,
    LIBSCOPE_ENABLE_DEMO_MODE: "true",
    LIBSCOPE_ENVIRONMENT: "desktop",
    LIBSCOPE_HOST: HOST,
    LIBSCOPE_LOG_LEVEL: "INFO",
    LIBSCOPE_PORT: String(PORT),
    PYTHONUNBUFFERED: "1",
  };

  if (app.isPackaged) {
    const executable = path.join(
      process.resourcesPath,
      "backend",
      `libscope-backend${process.platform === "win32" ? ".exe" : ""}`,
    );
    if (!fs.existsSync(executable)) {
      throw new Error(`The bundled LibScope backend is missing: ${executable}`);
    }
    return { command: executable, args: [], cwd: dataDirectory, env: environment };
  }

  const projectRoot = path.resolve(__dirname, "..");
  const python = process.env.LIBSCOPE_PYTHON || (process.platform === "win32" ? "python" : "python3");
  return {
    command: python,
    args: [path.join(projectRoot, "desktop", "backend.py")],
    cwd: projectRoot,
    env: environment,
  };
}

async function startBackend() {
  await assertPortAvailable();
  const dataDirectory = path.join(app.getPath("userData"), "data");
  fs.mkdirSync(dataDirectory, { recursive: true });
  backendLog = fs.createWriteStream(path.join(app.getPath("userData"), "backend.log"), { flags: "a" });
  backendLog.on("error", (error) => console.error("Could not write the LibScope backend log.", error));

  const { command, args, cwd, env } = getBackendCommand(dataDirectory);
  backendProcess = spawn(command, args, {
    cwd,
    env,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  backendProcess.stdout.on("data", (chunk) => backendLog.write(chunk));
  backendProcess.stderr.on("data", (chunk) => backendLog.write(chunk));
  backendProcess.on("error", (error) => {
    backendExit = { error };
    shutdownRequested = true;
    if (backendReady) {
      dialog.showErrorBox(
        "LibScope backend failed",
        `${error.message}\n\nBackend logs: ${path.join(app.getPath("userData"), "backend.log")}`,
      );
      app.quit();
    }
  });
  backendProcess.on("exit", (code, signal) => {
    backendExit = { code, signal };
    backendLog.end();
    if (backendReady && !shutdownRequested) {
      dialog.showErrorBox(
        "LibScope backend stopped",
        `The local service exited (${signal || code}). See ${path.join(app.getPath("userData"), "backend.log")}.`,
      );
      app.quit();
    }
  });

  await waitForBackend();
  backendReady = true;
}

async function waitForBackend() {
  const deadline = Date.now() + STARTUP_TIMEOUT_MS;
  let lastError;

  while (Date.now() < deadline) {
    if (backendExit) {
      const reason = backendExit.error?.message || backendExit.signal || backendExit.code;
      throw new Error(`The LibScope backend exited before becoming ready (${reason}).`);
    }

    let response;
    try {
      response = await fetch(`${APP_URL}/health`, { signal: AbortSignal.timeout(2000) });
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => setTimeout(resolve, STARTUP_RETRY_MS));
      continue;
    }

    if (response.ok) {
      const health = await response.json();
      if (health.service !== "libscope-api" || health.environment !== "desktop") {
        throw new Error("The local port is responding, but it is not the LibScope desktop service.");
      }
      return;
    }
    lastError = new Error(`The LibScope backend returned HTTP ${response.status}.`);
    await new Promise((resolve) => setTimeout(resolve, STARTUP_RETRY_MS));
  }

  throw new Error(`The LibScope backend did not become ready within ${STARTUP_TIMEOUT_MS / 1000} seconds. ${lastError?.message || ""}`);
}

async function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 960,
    minHeight: 680,
    show: false,
    autoHideMenuBar: true,
    backgroundColor: "#111812",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url === "about:blank") return { action: "allow" };
    try {
      if (new URL(url).origin === APP_URL) return { action: "allow" };
    } catch {
      return { action: "deny" };
    }
    if (url.startsWith("https://") || url.startsWith("http://")) {
      shell.openExternal(url).catch((error) => console.error("Could not open the external link.", error));
    }
    return { action: "deny" };
  });
  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (url === APP_URL || url.startsWith(`${APP_URL}/`) || url.startsWith(`${APP_URL}#`)) return;
    event.preventDefault();
    if (url.startsWith("https://") || url.startsWith("http://")) {
      shell.openExternal(url).catch((error) => console.error("Could not open the external link.", error));
    }
  });
  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  await mainWindow.loadURL(APP_URL);
  mainWindow.show();
}
