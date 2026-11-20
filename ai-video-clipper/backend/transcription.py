import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Generator
from faster_whisper import WhisperModel
from config import settings
from models import WordTimestamp, Segment, TranscriptionResult

logger = logging.getLogger(__name__)


class Transcriber:
    _model: Optional[WhisperModel] = None

    @classmethod
    def get_model(cls, model_name: Optional[str] = None) -> WhisperModel:
        if cls._model is None or (model_name and model_name != settings.whisper_model):
            model_to_load = model_name or settings.whisper_model
            logger.info(f"Loading Whisper model: {model_to_load} on {settings.whisper_device} ({settings.whisper_compute_type})")
            cls._model = WhisperModel(
                model_to_load,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                download_root=str(settings.data_dir / "models")
            )
            logger.info("Whisper model loaded successfully")
        return cls._model

    @classmethod
    def transcribe(
        cls,
        audio_path: str,
        model_name: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> TranscriptionResult:
        model = cls.get_model(model_name)

        if progress_callback:
            progress_callback(10, "Starting transcription...")

        segments_gen, info = model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        segments_list = []
        total_duration = info.duration

        for i, segment in enumerate(segments_gen):
            if progress_callback and total_duration > 0:
                progress = 10 + int((segment.end / total_duration) * 80)
                progress_callback(min(progress, 90), f"Transcribing... {int(segment.end)}s / {int(total_duration)}s")

            words = []
            if segment.words:
                for w in segment.words:
                    words.append(WordTimestamp(
                        word=w.word,
                        start=w.start,
                        end=w.end,
                        probability=w.probability
                    ))

            segments_list.append(Segment(
                id=i,
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
                words=words
            ))

        if progress_callback:
            progress_callback(95, "Finalizing transcription...")

        result = TranscriptionResult(
            language=info.language,
            language_probability=info.language_probability,
            duration=info.duration,
            segments=segments_list
        )

        if progress_callback:
            progress_callback(100, "Transcription complete")

        return result

    @classmethod
    def save_transcription(cls, result: TranscriptionResult, output_path: Path) -> None:
        data = {
            "language": result.language,
            "language_probability": result.language_probability,
            "duration": result.duration,
            "segments": [
                {
                    "id": s.id,
                    "start": s.start,
                    "end": s.end,
                    "text": s.text,
                    "words": [
                        {"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                        for w in s.words
                    ]
                }
                for s in result.segments
            ]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_transcription(cls, input_path: Path) -> TranscriptionResult:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return TranscriptionResult(
            language=data["language"],
            language_probability=data["language_probability"],
            duration=data["duration"],
            segments=[
                Segment(
                    id=s["id"],
                    start=s["start"],
                    end=s["end"],
                    text=s["text"],
                    words=[WordTimestamp(**w) for w in s["words"]]
                )
                for s in data["segments"]
            ]
        )