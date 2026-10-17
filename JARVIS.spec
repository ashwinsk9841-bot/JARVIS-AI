# -*- mode: python ; coding: utf-8 -*-
"""
JARVIS PyInstaller spec  (packaging layer only — no application code changes)

Release build (default):  single-file  dist/JARVIS/JARVIS.exe   (no console)
Debug build:              set env JARVIS_DEBUG=1  ->  onedir dist/JARVIS-DEBUG/  (console logs)

Resource strategy:
  - Bundled as data (read via Path(__file__), writable copies go to the one-file
    extraction dir which is rebuilt each launch):
        plugins/*.py               -> discovery by core/plugin_loader.py
        dashboard/static/*         -> served by dashboard/server.py
        config/jarvis.ico          -> window/app icon helper
  - Kept external next to the exe (read/write via frozen-aware BASE_DIR =
    Path(sys.executable).parent — NEVER embedded so secrets stay out of the exe):
        config/api_keys.json       memory/long_term.json   core/prompt.txt   face.png
  - The hiddenimports below cover modules that PyInstaller cannot see because the
    plugins are loaded at runtime by importlib (their third-party deps) and the
    optional TTS/STT engines imported lazily by the WhatsApp voice-bridge plugin.
"""

import os
from pathlib import Path

ROOT = Path(r"C:\JARVIS PERSON AGENT\jarvis-main\jarvis-main")
DEBUG = os.environ.get("JARVIS_DEBUG") == "1"
NAME = "JARVIS-DEBUG" if DEBUG else "JARVIS"
ICON = str(ROOT / "config" / "jarvis.ico")

datas = [
    (str(ROOT / "plugins" / "*.py"), "plugins"),
    (str(ROOT / "dashboard" / "static" / "*"), "dashboard/static"),
    (str(ROOT / "config" / "jarvis.ico"), "config"),
]

hiddenimports = [
    # Optional TTS / STT engines (imported lazily by plugins/whatsapp_voice_bridge.py)
    "core.stt",
    "core.tts",
    # Third-party deps used only by runtime-loaded plugins
    "winsdk",
    "soundcard",
    "uiautomation",
    "pyautogui",
    # ffmpeg-backed audio decode used by faster-whisper (reachable via core.stt)
    "av",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

if DEBUG:
    # One-folder, console-enabled build for verifying plugin discovery + logs.
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=True,
        icon=ICON,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name=NAME,
    )
else:
    # Release deliverable: a single JARVIS.exe, no console window.
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=ICON,
    )