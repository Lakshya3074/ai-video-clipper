from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoSource(BaseModel):
    type: Literal["upload", "url"]
    file_path: Optional[str] = None
    url: Optional[HttpUrl] = None
    original_filename: Optional[str] = None


class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    probability: float


class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: List[WordTimestamp]


class TranscriptionResult(BaseModel):
    language: str
    language_probability: float
    duration: float
    segments: List[Segment]


class ViralClip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    hook_reasoning: str
    virality_score: int = Field(ge=1, le=100)
    start_time: float
    end_time: float
    duration: float
    transcript: str


class ViralityAnalysis(BaseModel):
    clips: List[ViralClip]


class JobCreate(BaseModel):
    source: VideoSource
    whisper_model: Optional[str] = None
    clip_min_duration: Optional[int] = None
    clip_max_duration: Optional[int] = None
    caption_settings: Optional[dict] = None


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobProgress(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    current_step: str
    detail: Optional[str] = None
    clips: List[ViralClip] = []
    error: Optional[str] = None


class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    clips: List[ViralClip]
    output_files: List[str] = []
    created_at: datetime
    completed_at: Optional[datetime] = None


class ClipTrimUpdate(BaseModel):
    clip_id: str
    start_time: float
    end_time: float
    transcript: Optional[str] = None


class RenderRequest(BaseModel):
    job_id: str
    clips: List[ClipTrimUpdate]
    caption_overrides: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    whisper_model_loaded: bool
    ollama_available: bool
    version: str = "1.0.0"