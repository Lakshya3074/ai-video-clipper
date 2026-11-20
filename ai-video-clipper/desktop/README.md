# AI Video Clipper - Desktop App

Native desktop application for Windows, macOS, and Linux.

## Quick Start

### Option 1: Development Mode (Recommended for testing)

```bash
cd desktop

# Install dependencies
npm install

# Start development server (Vite + Tauri)
npm run tauri:dev
```

This opens a dev window with hot-reload. The backend runs as a sidecar process.

### Option 2: Build Production App

**Prerequisites:**
- Python 3.10+
- Node.js 18+
- Rust (install from https://rustup.rs)
- FFmpeg installed on system

```bash
cd desktop

# Install dependencies
npm install

# Build the app
python build.py

# Or manually:
# 1. Build backend sidecar
pip install pyinstaller
pyinstaller --onefile --name sidecar --add-data "backend:backend" sidecar_entry.py

# 2. Build frontend
npm run build

# 3. Build Tauri bundle
npm run tauri:build
```

Find your app in:
- **Windows**: `src-tauri/target/release/bundle/msi/` or `nsis/`
- **macOS**: `src-tauri/target/release/bundle/dmg/` or `app/`
- **Linux**: `src-tauri/target/release/bundle/appimage/` or `deb/`

---

## Project Structure

```
desktop/
├── src/                    # React frontend (Vite)
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── UploadArea.tsx
│   │   ├── JobProgress.tsx
│   │   ├── ClipStudio.tsx
│   │   └── Toast.tsx
│   ├── lib/utils.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── src-tauri/              # Tauri Rust backend
│   ├── src/main.rs         # Sidecar management, Tauri commands
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── icons/
├── backend/                # Python FastAPI (bundled as sidecar)
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── build.py                # Build automation
```

---

## How It Works

1. **Tauri Main Process (Rust)**: Manages the Python sidecar, creates the WebView window
2. **Python Sidecar**: Runs FastAPI backend on localhost:8000
3. **React Frontend**: Communicates with Python backend via HTTP/WebSocket

```
┌─────────────────┐
│   Tauri (Rust)  │
│  - Window Mgmt  │
│  - Sidecar Mgmt │
│  - System APIs  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────────┐
│ React │ │ Python    │
│ (Vite)│ │ FastAPI   │
│       │ │ +Whisper  │
│       │ │ +FFmpeg   │
└───────┘ └───────────┘
```

---

## Configuration

### `tauri.conf.json`

Key settings:
- `productName`: App name shown to users
- `identifier`: Bundle ID (com.ai-video-clipper.app)
- `bundle.resources`: Bundles the Python backend
- `bundle.externalBin`: Includes the sidecar binary

### Environment Variables

The app sets these automatically for the sidecar:
- `HOST=127.0.0.1`
- `PORT=8000`
- `DATA_DIR=$HOME/ai-video-clipper`

For cloud LLM (required for desktop app since no local Ollama):
- Set `OPENAI_API_KEY`, `OPENAI_BASE_URL` in your system env or `.env` file

---

## Features

| Feature | Desktop App | Web Version |
|---------|-------------|-------------|
| File Upload | ✅ Native picker + drag-drop | ✅ Drag-drop + URL |
| URL Download | ✅ yt-dlp bundled | ✅ yt-dlp |
| Transcription | ✅ faster-whisper (CPU) | ✅ faster-whisper |
| Face Tracking | ✅ OpenCV bundled | ✅ MediaPipe |
| Captions | ✅ FFmpeg libass | ✅ FFmpeg libass |
| LLM Analysis | ⚠️ Requires cloud API key | ⚠️ Requires cloud API key |
| Offline Use | ✅ (with downloaded model) | ✅ (with local Ollama) |
| System Tray | ✅ (can be added) | ❌ |
| Auto-updates | ✅ (Tauri updater) | ❌ |

---

## Adding a Cloud LLM Key

The desktop app requires a cloud LLM API key (Groq/OpenRouter/Gemini) since it can't run local Ollama easily.

**Get a free key:**
- **Groq**: https://console.groq.com/keys (14,400 req/day, Llama 3.1 8B)
- **OpenRouter**: https://openrouter.ai/keys (many free models)
- **Google Gemini**: https://aistudio.google.com/apikey (1,500 req/day)

**Set the key:**

Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="gsk_your_key"
$env:OPENAI_BASE_URL="https://api.groq.com/openai/v1"
$env:OPENAI_MODEL="llama-3.1-8b-instant"
$env:LLM_PROVIDER="openai_compatible"
```

macOS/Linux:
```bash
export OPENAI_API_KEY="gsk_your_key"
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
export OPENAI_MODEL="llama-3.1-8b-instant"
export LLM_PROVIDER="openai_compatible"
```

Or create a `.env` file in the app's data directory.

---

## Troubleshooting

### "Sidecar failed to start"
- Check that FFmpeg is installed: `ffmpeg -version`
- Ensure Python dependencies are bundled (check `build.py`)

### "No module named 'faster_whisper'"
- The sidecar build should bundle all deps from `requirements.txt`
- Re-run `python build.py`

### "Port 8000 already in use"
- Change `PORT` in `tauri.conf.json` or kill existing process

### "LLM connection refused"
- Set cloud API keys as environment variables (see above)
- Desktop app can't use local Ollama by default

### Build fails on Windows
- Install Visual Studio Build Tools: `winget install Microsoft.VisualStudio.2022.BuildTools`
- Install Rust: `winget install Rustlang.Rustup`

### Build fails on macOS
- Install Xcode command line tools: `xcode-select --install`

### Build fails on Linux
- Install dependencies: `sudo apt install libwebkit2gtk-4.0-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev`

---

## Distributing Your App

### Windows
- MSI installer (default)
- NSIS installer (alternative)
- Portable EXE (configure in `tauri.conf.json`)

### macOS
- DMG (disk image)
- App Bundle (.app)
- Notarization required for distribution outside App Store

### Linux
- AppImage (universal)
- .deb (Debian/Ubuntu)
- .rpm (Fedora/openSUSE)

---

## Next Steps

1. **Test in dev mode**: `npm run tauri:dev`
2. **Build for your platform**: `python build.py`
3. **Test the built app**: Run from `src-tauri/target/release/bundle/`
4. **Distribute**: Share the installer with users

For production, consider:
- Code signing (Windows/macOS)
- Auto-updates (configure `tauri.conf.json` updater)
- Custom icons (replace files in `src-tauri/icons/`)