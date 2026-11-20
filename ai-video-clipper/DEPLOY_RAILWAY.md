# Deploy to Railway (Free Tier) 🚀

Railway is the easiest way to deploy this app — it handles Docker, volumes, custom domains, and gives you **$5/month free credit** (enough for 24/7 hobby usage).

---

## Prerequisites

1. **GitHub account** (to connect repo)
2. **Railway account** — sign up at [railway.app](https://railway.app) with GitHub
3. **Free LLM API key** — get one from:
   - **Groq** (recommended): https://console.groq.com/keys → 14,400 req/day
   - **OpenRouter**: https://openrouter.ai/keys → many free models
   - **Google AI Studio**: https://aistudio.google.com/apikey → Gemini 1.5 Flash

---

## Step 1: Push to GitHub

```bash
# In your project folder (where docker-compose.yml lives)
git init
git add .
git commit -m "Initial commit: AI Video Clipper"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-video-clipper.git
git push -u origin main
```

---

## Step 2: Create Railway Project

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `ai-video-clipper` repo
4. Railway auto-detects `railway.toml` and creates **two services**:
   - `backend` (port 8000)
   - `frontend` (port 3000)

---

## Step 3: Add Environment Variables

In Railway dashboard → **Backend service** → **Variables** tab, add:

| Variable | Value | Required |
|----------|-------|----------|
| `OPENAI_API_KEY` | `gsk_your_groq_key` (or OpenRouter/Gemini key) | **YES** |
| `OPENAI_BASE_URL` | `https://api.groq.com/openai/v1` | **YES** |
| `OPENAI_MODEL` | `llama-3.1-8b-instant` | **YES** |
| `LLM_PROVIDER` | `openai_compatible` | **YES** |

> **Tip**: Copy from `backend/.env.production.example`

---

## Step 4: Add Persistent Volume

1. In Railway dashboard → **Backend service** → **Settings** → **Volumes**
2. Click **"Add Volume"**
3. Mount path: `/app/data`
4. This persists uploads, outputs, and Whisper model cache across deployments

---

## Step 5: Deploy!

1. Railway auto-builds on push — watch the **Deployments** tab
2. First deploy takes ~3-5 mins (installs FFmpeg, downloads Whisper model)
3. Once deployed, click the **generated domain** (e.g., `ai-video-clipper.up.railway.app`)

---

## Step 6: Custom Domain (Optional)

1. Backend service → **Settings** → **Domains** → **"Custom Domain"**
2. Add your domain (e.g., `clipper.yourdomain.com`)
3. Railway gives you CNAME target → add to your DNS
4. Repeat for Frontend service if desired

---

## Free Tier Limits

| Resource | Limit |
|----------|-------|
| **Monthly Credit** | $5 (resets 1st of month) |
| **RAM** | 512 MB - 1 GB per service |
| **CPU** | Shared vCPU |
| **Disk** | 1 GB + volumes |
| **Network** | 100 GB/month egress |
| **Build Minutes** | 500/month |

> With `MAX_CONCURRENT_JOBS=1` and `WHISPER_MODEL=base`, this fits comfortably in free tier.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `OOMKilled` / Out of memory | Reduce `WHISPER_MODEL=tiny`, set `MAX_CONCURRENT_JOBS=1` |
| `yt-dlp` fails on YouTube | YouTube blocks some cloud IPs — use local files or try different URL |
| Whisper model re-downloads | Ensure `/app/data` volume is mounted and persists |
| Frontend can't reach backend | Check `NEXT_PUBLIC_API_BASE=http://backend:8000` in frontend env |
| Build timeout | First build downloads ~500MB — wait or increase timeout in Railway settings |

---

## Local Testing with Docker

```bash
# Build and run locally (mirrors Railway)
docker compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

---

## Alternative: Deploy Backend Only

If you want to host frontend on **Vercel** (free, fast CDN) and backend on Railway:

1. Deploy backend to Railway as above
2. In Vercel, import frontend folder → set `NEXT_PUBLIC_API_BASE=https://your-backend.railway.app`
3. Vercel handles frontend, Railway handles video processing

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Issues: GitHub Issues on your repo