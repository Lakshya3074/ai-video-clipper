import os
import asyncio
import uuid
import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Set

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from models import (
    JobCreate, JobResponse, JobProgress, JobResult, JobStatus,
    ViralClip, ClipTrimUpdate, RenderRequest, HealthResponse,
    VideoSource, TranscriptionResult
)
from transcription import Transcriber
from virality import ViralityAnalyzer
from processing import VideoDownloader, VideoRenderer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

jobs: Dict[str, dict] = {}
active_jobs: Set[str] = set()
job_lock = asyncio.Lock()
virality_analyzer = ViralityAnalyzer()
video_renderer = VideoRenderer()


def update_job_progress(job_id: str, status: JobStatus, progress: int, step: str, detail: str = None, clips: List[ViralClip] = None, error: str = None):
    if job_id in jobs:
        jobs[job_id]['progress'] = JobProgress(
            job_id=job_id,
            status=status,
            progress=progress,
            current_step=step,
            detail=detail,
            clips=clips or [],
            error=error
        )


async def process_job(job_id: str, job_data: dict):
    async with job_lock:
        if len(active_jobs) >= settings.max_concurrent_jobs:
            jobs[job_id]['status'] = 'queued'
            return
        active_jobs.add(job_id)
        jobs[job_id]['status'] = 'running'

    try:
        source = job_data['source']
        clip_min = job_data.get('clip_min_duration', settings.clip_min_duration)
        clip_max = job_data.get('clip_max_duration', settings.clip_max_duration)
        whisper_model = job_data.get('whisper_model')
        caption_settings = job_data.get('caption_settings', {})

        job_dir = settings.temp_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        video_path = None

        # Step 1: Get video file
        update_job_progress(job_id, JobStatus.DOWNLOADING, 5, "Downloading video...")
        if source.type == "url":
            video_path = VideoDownloader.download(
                str(source.url),
                job_dir,
                lambda p, m: update_job_progress(job_id, JobStatus.DOWNLOADING, p, m)
            )
        else:
            video_path = Path(source.file_path)
            if not video_path.exists():
                raise FileNotFoundError(f"Uploaded file not found: {video_path}")
            update_job_progress(job_id, JobStatus.DOWNLOADING, 100, "Video ready")

        # Step 2: Extract audio
        update_job_progress(job_id, JobStatus.TRANSCRIBING, 10, "Extracting audio...")
        audio_path = job_dir / "audio.wav"
        video_renderer.extract_audio(video_path, audio_path)

        # Step 3: Transcribe
        update_job_progress(job_id, JobStatus.TRANSCRIBING, 15, "Transcribing with Whisper...")
        transcription = Transcriber.transcribe(
            str(audio_path),
            model_name=whisper_model,
            lambda p, m: update_job_progress(job_id, JobStatus.TRANSCRIBING, 15 + int(p * 0.5), m)
        )

        # Save transcription for later editing
        Transcriber.save_transcription(transcription, job_dir / "transcription.json")

        # Step 4: Analyze for viral clips
        update_job_progress(job_id, JobStatus.ANALYZING, 60, "Analyzing for viral moments...")
        analysis = await virality_analyzer.analyze(
            transcription,
            lambda p, m: update_job_progress(job_id, JobStatus.ANALYZING, 60 + int(p * 0.3), m)
        )

        # Filter clips by duration
        filtered_clips = [
            c for c in analysis.clips
            if clip_min <= c.duration <= clip_max
        ][:5]

        if not filtered_clips:
            raise ValueError("No suitable viral clips found in the video")

        jobs[job_id]['clips'] = filtered_clips
        jobs[job_id]['transcription'] = transcription
        jobs[job_id]['video_path'] = str(video_path)
        jobs[job_id]['words_by_segment'] = [
            [w.model_dump() for w in s.words] for s in transcription.segments
        ]

        update_job_progress(job_id, JobStatus.ANALYZING, 95, f"Found {len(filtered_clips)} viral clips")
        await asyncio.sleep(0.5)
        update_job_progress(job_id, JobStatus.COMPLETED, 100, "Analysis complete", clips=filtered_clips)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        update_job_progress(job_id, JobStatus.FAILED, 0, "Failed", error=str(e))
        jobs[job_id]['error'] = str(e)
    finally:
        active_jobs.discard(job_id)
        # Check queue
        await process_queue()


async def process_queue():
    async with job_lock:
        for job_id, job in jobs.items():
            if job.get('status') == 'queued':
                asyncio.create_task(process_job(job_id, job))
                break


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Video Clipper backend...")
    Transcriber.get_model()
    yield
    await virality_analyzer.close()
    logger.info("Shutdown complete")


app = FastAPI(title="AI Video Clipper", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve output files
app.mount("/outputs", StaticFiles(directory=str(settings.outputs_dir)), name="outputs")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    ollama_ok = False
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = resp.status_code == 200
    except:
        pass

    return HealthResponse(
        status="healthy",
        whisper_model_loaded=True,
        ollama_available=ollama_ok
    )


@app.post("/jobs", response_model=JobResponse)
async def create_job(
    background_tasks: BackgroundTasks,
    source_type: str = Form(...),
    file: UploadFile = File(None),
    url: str = Form(None),
    whisper_model: str = Form(None),
    clip_min_duration: int = Form(None),
    clip_max_duration: int = Form(None)
):
    job_id = str(uuid.uuid4())[:12]

    if source_type == "upload":
        if not file:
            raise HTTPException(400, "File required for upload")
        upload_path = settings.uploads_dir / f"{job_id}_{file.filename}"
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        source = VideoSource(type="upload", file_path=str(upload_path), original_filename=file.filename)
    elif source_type == "url":
        if not url:
            raise HTTPException(400, "URL required for url source")
        source = VideoSource(type="url", url=url)
    else:
        raise HTTPException(400, "Invalid source type")

    job_data = {
        'source': source,
        'whisper_model': whisper_model,
        'clip_min_duration': clip_min_duration,
        'clip_max_duration': clip_max_duration
    }

    jobs[job_id] = {
        'id': job_id,
        'data': job_data,
        'status': 'pending',
        'created_at': datetime.utcnow(),
        'progress': JobProgress(job_id=job_id, status=JobStatus.PENDING, progress=0, current_step="Queued"),
        'clips': [],
        'transcription': None,
        'video_path': None
    }

    background_tasks.add_task(process_job, job_id, job_data)

    return JobResponse(job_id=job_id, status=JobStatus.PENDING, message="Job queued")


@app.get("/jobs/{job_id}/progress", response_model=JobProgress)
async def get_job_progress(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]['progress']


@app.websocket("/jobs/{job_id}/ws")
async def job_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            if job_id in jobs:
                progress = jobs[job_id]['progress']
                await websocket.send_json(progress.model_dump())
                if progress.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    break
            else:
                await websocket.send_json({"error": "Job not found"})
                break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@app.get("/jobs/{job_id}/result", response_model=JobResult)
async def get_job_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    return JobResult(
        job_id=job_id,
        status=job['progress'].status,
        clips=job.get('clips', []),
        output_files=[],
        created_at=job['created_at'],
        completed_at=datetime.utcnow() if job['progress'].status == JobStatus.COMPLETED else None
    )


@app.post("/jobs/{job_id}/render")
async def render_clips(job_id: str, request: RenderRequest, background_tasks: BackgroundTasks):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    job = jobs[job_id]
    if not job.get('clips'):
        raise HTTPException(400, "No clips to render")

    video_path = Path(job['video_path'])
    transcription = job['transcription']
    words_by_segment = job['words_by_segment']

    clip_map = {c.id: c for c in job['clips']}

    for update in request.clips:
        if update.clip_id in clip_map:
            clip_map[update.clip_id].start_time = update.start_time
            clip_map[update.clip_id].end_time = update.end_time
            clip_map[update.clip_id].duration = update.end_time - update.start_time
            if update.transcript:
                clip_map[update.clip_id].transcript = update.transcript

    updated_clips = list(clip_map.values())

    output_dir = settings.outputs_dir / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    def progress_wrapper(p, m):
        update_job_progress(job_id, JobStatus.RENDERING, p, m)

    def get_words_for_clip(clip: ViralClip) -> List[dict]:
        all_words = []
        for seg_words in words_by_segment:
            for w in seg_words:
                if clip.start_time <= w['start'] < clip.end_time:
                    all_words.append(w)
        return all_words

    def render_task():
        try:
            clip_words = [get_words_for_clip(c) for c in updated_clips]
            video_renderer.render_all_clips(
                video_path,
                updated_clips,
                clip_words,
                output_dir,
                progress_wrapper
            )
            update_job_progress(job_id, JobStatus.COMPLETED, 100, "All clips rendered!")
        except Exception as e:
            logger.error(f"Render failed: {e}")
            update_job_progress(job_id, JobStatus.FAILED, 0, "Render failed", error=str(e))

    background_tasks.add_task(render_task)

    return {"message": "Render started", "job_id": job_id}


@app.get("/jobs/{job_id}/clips/{clip_id}/preview")
async def get_clip_preview(job_id: str, clip_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    clip_dir = settings.outputs_dir / job_id / clip_id
    mp4_files = list(clip_dir.glob("*.mp4"))
    if not mp4_files:
        raise HTTPException(404, "Clip not yet rendered")
    return FileResponse(mp4_files[0], media_type="video/mp4")


@app.get("/jobs/{job_id}/transcription")
async def get_transcription(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    transcription = jobs[job_id].get('transcription')
    if not transcription:
        raise HTTPException(404, "Transcription not available")
    return transcription


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)