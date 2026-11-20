# ⚡ FASTEST WAY TO RUN AI VIDEO CLIPPER

## Option A: Local Run (5 mins setup, 100% free forever)

### Windows (PowerShell - run as admin first time):
```powershell
# 1. Install prerequisites (one-time)
winget install Python.Python.3.10 Git.Git FFmpeg.GPL.NodeJS
refreshenv

# 2. Clone and run
cd $HOME
git clone https://github.com/YOU/ai-video-clipper.git  # or unzip this folder
cd ai-video-clipper\backend

# 3. Install Python deps
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Start backend
python main.py

# NEW TERMINAL: Start frontend
cd ..\frontend
npm install
npm run dev

# Open http://localhost:3000
```

### macOS (Terminal):
```bash
# 1. Install prerequisites
brew install python@3.10 node ffmpeg

# 2. Clone and run
cd ~
git clone https://github.com/YOU/ai-video-clipper.git
cd ai-video-clipper/backend

# 3. Install Python deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Start backend
python main.py

# NEW TERMINAL: Start frontend
cd ../frontend
npm install
npm run dev

# Open http://localhost:3000
```

### Linux (Ubuntu/Debian):
```bash
# 1. Install prerequisites
sudo apt update && sudo apt install -y python3.10 python3-pip nodejs npm ffmpeg

# 2. Clone and run
cd ~
git clone https://github.com/YOU/ai-video-clipper.git
cd ai-video-clipper/backend

# 3. Install Python deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Start backend
python main.py

# NEW TERMINAL: Start frontend
cd ../frontend
npm install
npm run dev

# Open http://localhost:3000
```

---

## Option B: Railway Deploy (3 mins, free tier, online instantly)

```bash
# 1. Push to GitHub
git init && git add . && git commit -m "AI Video Clipper"
git branch -M main
git remote add origin https://github.com/YOUR_USER/ai-video-clipper.git
git push -u origin main

# 2. Go to https://railway.app
#    - New Project → Deploy from GitHub → Select repo
#    - Backend service → Variables → Add:
#      OPENAI_API_KEY=gsk_get_from_groq
#      OPENAI_BASE_URL=https://api.groq.com/openai/v1
#      OPENAI_MODEL=llama-3.1-8b-instant
#      LLM_PROVIDER=openai_compatible
#    - Backend → Settings → Volumes → Add /app/data
#    - Deploy!

# 3. Get your URL like https://ai-video-clipper.up.railway.app
```

**Get FREE Groq API key (30 seconds):**
1. Go to https://console.groq.com/keys
2. Sign up with Google/GitHub
3. Copy your key
4. Paste into Railway variables

---

## Option C: Docker (2 commands, works everywhere)

```bash
# Requires: Docker Desktop installed

# 1. Get Groq key from https://console.groq.com/keys

# 2. Run everything
cd ai-video-clipper
OPENAI_API_KEY=gsk_your_key_here \
OPENAI_BASE_URL=https://api.groq.com/openai/v1 \
OPENAI_MODEL=llama-3.1-8b-instant \
LLM_PROVIDER=openai_compatible \
docker compose up --build

# Open http://localhost:3000
```

---

## 🎯 Fastest Path Summary

| Method | Time | Cost | Best For |
|--------|------|------|----------|
| **Local (Option A)** | 5 min setup | $0 | Testing, privacy, no limits |
| **Railway (Option B)** | 3 min deploy | $0 free tier | Sharing, online access |
| **Docker (Option C)** | 2 commands | $0 | Consistent across machines |

---

## 🔑 Get FREE API Key (Required for cloud deploy)

**Groq (recommended - fastest, 14,400 req/day free):**
1. https://console.groq.com/keys
2. Sign up (Google/GitHub)
3. Copy key (starts with `gsk_`)
4. Use in Railway/Docker env vars

**OpenRouter (many free models):**
1. https://openrouter.ai/keys
2. Sign up
3. Copy key

---

## ✅ Verify It Works

After running, open **http://localhost:3000** (or your Railway URL):
1. Upload a video or paste YouTube URL
2. Watch progress: Downloading → Transcribing → Analyzing → Rendering
3. Get 3-5 viral clips with scores
4. Export MP4s with captions

---

**Questions?** Check `README.md` for full docs.