import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Literal


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Paths
    data_dir: Path = Path("./data")
    uploads_dir: Path = Path("./data/uploads")
    outputs_dir: Path = Path("./data/outputs")
    temp_dir: Path = Path("./data/temp")

    # Whisper
    whisper_model: str = "base"  # tiny, base, small, medium, large-v3
    whisper_device: Literal["cpu", "cuda"] = "cpu"
    whisper_compute_type: Literal["int8", "float16", "float32"] = "int8"

    # LLM (Ollama by default, or OpenAI-compatible endpoint)
    llm_provider: Literal["ollama", "openai_compatible"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"  # or qwen2.5:7b, mistral:7b
    openai_base_url: Optional[str] = None  # e.g., https://api.groq.com/openai/v1
    openai_api_key: Optional[str] = None
    openai_model: str = "llama-3.1-8b-instant"

    # Video processing
    target_width: int = 1080
    target_height: int = 1920
    target_fps: int = 30
    clip_min_duration: int = 30
    clip_max_duration: int = 60

    # Face tracking
    face_detection_confidence: float = 0.5
    face_smoothing_frames: int = 5

    # Caption styling
    caption_font: str = "Arial"
    caption_font_size: int = 80
    caption_color: str = "#FFFFFF"
    caption_highlight_color: str = "#FFD700"
    caption_outline_color: str = "#000000"
    caption_outline_width: int = 3
    caption_margin_v: int = 150

    # Processing limits
    max_concurrent_jobs: int = 2
    job_timeout_seconds: int = 3600

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


settings = Settings()

# Ensure directories exist
for path in [settings.data_dir, settings.uploads_dir, settings.outputs_dir, settings.temp_dir]:
    path.mkdir(parents=True, exist_ok=True)