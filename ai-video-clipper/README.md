# AI Video Clipper 🎬

Transform long-form videos into viral short-form clips (9:16 vertical) with dynamic "Hormozi-style" captions — **100% free, runs locally, zero API keys required**.

![AI Video Clipper Demo](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Node](https://img.shields.io/badge/Node-18%2B-green)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🎥 Zero-Cost Ingestion** | Local file uploads (MP4/MOV/MKV/WebM) + YouTube/video URL downloads via `yt-dlp` |
| **🎤 Local Transcription** | `faster-whisper` (CPU/GPU) — word-level timestamps, no cloud, no limits |
| **🧠 Free AI Virality Engine** | Local LLM via **Ollama** (Llama 3.1, Qwen 2.5, Mistral) — finds top 3-5 viral hooks with scores |
| **📱 Smart 9:16 Auto-Reframe** | Face tracking (MediaPipe/OpenCV) keeps speaker centered when cropping 16:9 → 9:16 |
| **✨ Dynamic Captions** | Word-by-word animated `.ass` subtitles burned in via FFmpeg (Hormozi-style) |
| **🎛️ Interactive Clip Studio** | In-browser preview, trim timestamps, edit transcripts, batch export MP4s |
| **⚡ Real-time Progress** | WebSocket + polling: "Downloading..." → "Transcribing..." → "Analyzing..." → "Rendering..." |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Backend       │
│   (Next.js 14)  │◄───►│   (FastAPI)     │
│   Port 3000     │     │   Port 8000     │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
   ┌───────────┐          ┌───────────┐          ┌───────────┐
   │ yt-dlp    │          │faster-    │          │ FFmpeg    │
   │ (download)│          │whisper    │          │ (crop,    │
   └───────────┘          │ (STT)     │          │  captions)│
                          └───────────┘          └───────────┘
                                 ▲
                                 │
                          ┌───────────────┐
                          │ Ollama        │
                          │ (LLM Analysis)│
                          └───────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| **Python** | 3.10+ | [python.org](https://python.org) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org) |
| **FFmpeg** | 4.4+ (with libass) | `winget install ffmpeg` / `brew install ffmpeg` / `apt install ffmpeg` |
| **Ollama** | Latest | [ollama.ai](https://ollama.ai) |

> **FFmpeg must include `libass`** for subtitle burning (standard in most packages).

---

### 1️⃣ Install & Start Ollama (Local LLM — 100% Free)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start server (keep running in background)
ollama serve

# In another terminal, pull a model (choose ONE):
# Option A: Llama 3.1 8B (recommended, best quality)
ollama pull llama3.1:8b

# Option B: Qwen 2.5 7B (excellent multilingual)
ollama pull qwen2.5:7b

# Option C: Mistral 7B (fast, efficient)
ollama pull mistral:7b

# Option D: Phi-3 Medium (small but capable)
ollama pull phi3:medium
```

> **Verify**: `curl http://localhost:11434/api/tags` should show your model.

---

### 2️⃣ Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env if needed (defaults work for Ollama)

# Start server
python main.py
```

Server runs at **http://localhost:8000** — check health at `/health`.

---

### 3️⃣ Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at **http://localhost:3000**.

---

### 4️⃣ Use It!

1. Open **http://localhost:3000**
2. **Upload** a video file (drag & drop) **OR** paste a **YouTube/video URL**
3. Click **"Analyze Video"** — watch real-time progress
4. Review **3-5 viral clips** with scores, titles, and reasoning
5. **Adjust** start/end times, edit transcripts in the studio
6. Click **"Export All"** — get MP4s with burned-in dynamic captions!

---

## ⚙️ Configuration

### Backend `.env` (copy from `.env.example`)

```ini
# Server
HOST=0.0.0.0
PORT=8000

# Whisper (STT)
WHISPER_MODEL=base        # tiny, base, small, medium, large-v3
WHISPER_DEVICE=cpu        # cpu or cuda
WHISPER_COMPUTE_TYPE=int8 # int8, float16, float32

# LLM Provider
LLM_PROVIDER=ollama       # or "openai_compatible"
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Optional: Free-tier cloud LLM fallback (Groq, OpenRouter, Gemini, etc.)
# OPENAI_BASE_URL=https://api.groq.com/openai/v1
# OPENAI_API_KEY=your_free_key
# OPENAI_MODEL=llama-3.1-8b-instant

# Video Output
TARGET_WIDTH=1080
TARGET_HEIGHT=1920
TARGET_FPS=30
CLIP_MIN_DURATION=30
CLIP_MAX_DURATION=60

# Captions
CAPTION_FONT_SIZE=80
CAPTION_COLOR=#FFFFFF
CAPTION_HIGHLIGHT_COLOR=FFD700
```

### Whisper Model Selection

| Model | Size | Speed (CPU) | Accuracy | RAM |
|-------|------|-------------|----------|-----|
| `tiny` | 39 MB | ~8x realtime | Low | ~1 GB |
| `base` | 74 MB | ~4x realtime | Good | ~1.5 GB |
| `small` | 244 MB | ~2x realtime | Better | ~3 GB |
| `medium` | 769 MB | ~1x realtime | High | ~6 GB |
| `large-v3` | 1550 MB | ~0.5x realtime | Best | ~10 GB |

> **Recommendation**: `base` for most uses. Use `small`/`medium` if you have RAM.

### Free Cloud LLM Options (if no Ollama)

| Provider | Free Tier | Model | Base URL |
|----------|-----------|-------|----------|
| **Groq** | 14,400 req/day | Llama 3.1 8B Instant | `https://api.groq.com/openai/v1` |
| **OpenRouter** | Many free models | Various | `https://openrouter.ai/api/v1` |
| **Google AI Studio** | 1500 req/day | Gemini 1.5 Flash | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| **Together AI** | $1 free credit | Many | `https://api.together.xyz/v1` |

Set in `.env`:
```ini
LLM_PROVIDER=openai_compatible
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=gsk_xxxxxxxxxxxx
OPENAI_MODEL=llama-3.1-8b-instant
```

---

## 📁 Project Structure

```
ai-video-clipper/
├── backend/
│   ├── main.py              # FastAPI app, endpoints, job queue
│   ├── config.py            # Pydantic settings (.env)
│   ├── models.py            # Pydantic models (Job, Clip, Transcription)
│   ├── transcription.py     # faster-whisper wrapper
│   ├── virality.py          # Ollama/OpenAI-compatible LLM client
│   ├── processing.py        # yt-dlp, face tracking, FFmpeg rendering
│   ├── requirements.txt     # Python deps
│   ├── .env.example         # Config template
│   └── data/                # Runtime data (uploads, outputs, temp)
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx     # Main page (upload + studio)
│   │   │   ├── layout.tsx   # Root layout
│   │   │   └── globals.css  # Tailwind + CSS variables
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── UploadArea.tsx
│   │   │   ├── JobProgress.tsx
│   │   │   ├── ClipStudio.tsx
│   │   │   └── Toast.tsx
│   │   └── lib/utils.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── postcss.config.js
│
└── README.md
```

---

## 🔧 API Reference

### Create Job
```bash
POST /jobs
Content-Type: multipart/form-data

# Upload file:
source_type=upload&file=@video.mp4

# Or URL:
source_type=url&url=https://youtube.com/watch?v=...
```

### Get Progress (polling)
```bash
GET /jobs/{job_id}/progress
# Returns: { job_id, status, progress, current_step, detail, clips[], error }
```

### WebSocket Progress (real-time)
```bash
WS /jobs/{job_id}/ws
```

### Get Result
```bash
GET /jobs/{job_id}/result
```

### Render Clips
```bash
POST /jobs/{job_id}/render
Content-Type: application/json

{
  "job_id": "...",
  "clips": [
    { "clip_id": "abc123", "start_time": 12.5, "end_time": 58.3, "transcript": "edited text" }
  ]
}
```

### Preview Clip
```bash
GET /jobs/{job_id}/clips/{clip_id}/preview
# Returns MP4 video
```

---

## 🐳 Docker (Local Development)

```bash
# Build and run locally
docker compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

> Requires local Ollama running on host. For GPU support, ensure NVIDIA Container Toolkit is installed.

---

## ☁️ Deploy to Railway (Free Cloud Hosting)

**Recommended for free online hosting** — Railway gives $5/month credit, auto-deploys from GitHub, supports persistent volumes.

### Quick Deploy

1. **Push to GitHub**:
   ```bash
   git init && git add . && git commit -m "Initial commit"
   git branch -M main && git remote add origin https://github.com/YOUR_USER/ai-video-clipper.git
   git push -u origin main
   ```

2. **Create Railway Project**:
   - Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
   - Select your repo — Railway detects `railway.toml` and creates backend + frontend services

3. **Add Environment Variables** (Backend service → Variables):
   | Variable | Value |
   |----------|-------|
   | `OPENAI_API_KEY` | Your free Groq/OpenRouter/Gemini key |
   | `OPENAI_BASE_URL` | `https://api.groq.com/openai/v1` (or OpenRouter/Gemini URL) |
   | `OPENAI_MODEL` | `llama-3.1-8b-instant` |
   | `LLM_PROVIDER` | `openai_compatible` |

   > Get FREE keys: **Groq** (14,400 req/day) → [console.groq.com](https://console.groq.com/keys) | **OpenRouter** → [openrouter.ai](https://openrouter.ai/keys) | **Google Gemini** → [aistudio.google.com](https://aistudio.google.com/apikey)

4. **Add Persistent Volume** (Backend → Settings → Volumes):
   - Mount path: `/app/data` — persists uploads, outputs, Whisper cache

5. **Deploy** — Railway builds and gives you a public URL (e.g., `https://ai-video-clipper.up.railway.app`)

### Free Tier Limits
- $5/month credit (resets 1st)
- 512MB-1GB RAM per service
- 1GB disk + volumes
- 100GB egress/month

See `DEPLOY_RAILWAY.md` for detailed guide, troubleshooting, and Vercel frontend alternative.

---

## 🐳 Docker Compose (with Local Ollama + GPU)

For local development with full local stack (Ollama + GPU):

---

## 🧪 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: faster_whisper` | `pip install -r requirements.txt` in venv |
| `yt-dlp: command not found` | `pip install yt-dlp` |
| `FFmpeg: libass not found` | Reinstall FFmpeg with libass (`brew install ffmpeg` / `apt install ffmpeg`) |
| `Ollama connection refused` | Run `ollama serve` in terminal |
| `CUDA out of memory` | Set `WHISPER_COMPUTE_TYPE=int8` and `WHISPER_MODEL=base` |
| `Port 8000/3000 in use` | Change `PORT` in `.env` or kill existing process |
| `WebSocket connection failed` | Frontend falls back to polling automatically |
| `No clips found` | Video may be too short or lack speech; try longer content |

---

## 🎯 Tips for Best Results

1. **Video Length**: 5-60 minutes works best (podcasts, interviews, tutorials)
2. **Audio Quality**: Clear speech → better transcription → better clips
3. **Whisper Model**: `base` = good balance; `small`/`medium` for noisy audio
4. **Face Tracking**: Works best with single speaker facing camera
5. **Caption Style**: Adjust `CAPTION_FONT_SIZE`, colors in `.env` for your brand
6. **LLM Prompt**: Edit `SYSTEM_PROMPT` in `backend/virality.py` to tune virality criteria

---

## 📝 License

MIT License — free for personal and commercial use.

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 🙏 Acknowledgments

- **[faster-whisper](https://github.com/guillaumekln/faster-whisper)** — blazing fast local STT
- **[Ollama](https://ollama.ai)** — local LLM made simple
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — universal video downloader
- **[FFmpeg](https://ffmpeg.org)** — video processing backbone
- **[MediaPipe](https://mediapipe.dev)** — face detection
- **[Next.js](https://nextjs.org)** + **[Tailwind CSS](https://tailwindcss.com)** — frontend stack

---

**Built with ❤️ for creators who want viral clips without the subscription fees.**