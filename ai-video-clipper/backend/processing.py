import os
import subprocess
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Generator
import cv2
import numpy as np
import yt_dlp
from config import settings
from models import ViralClip, JobProgress, JobStatus

logger = logging.getLogger(__name__)


class VideoDownloader:
    @staticmethod
    def download(url: str, output_path: Path, progress_callback: Optional[callable] = None) -> Path:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [],
        }

        if progress_callback:
            def hook(d):
                if d['status'] == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    if total > 0:
                        pct = int((downloaded / total) * 100)
                        progress_callback(min(pct, 95), f"Downloading... {pct}%")
                elif d['status'] == 'finished':
                    progress_callback(95, "Download complete, processing...")

            ydl_opts['progress_hooks'] = [hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp4'):
                for f in output_path.glob(f"{Path(filename).stem}.*"):
                    if f.suffix in ['.mp4', '.mkv', '.webm']:
                        filename = str(f)
                        break

        downloaded_file = Path(filename)
        if not downloaded_file.exists():
            raise FileNotFoundError(f"Downloaded file not found: {filename}")

        return downloaded_file


class FaceTracker:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.mp_face = None
        self._init_mediapipe()

    def _init_mediapipe(self):
        try:
            import mediapipe as mp
            self.mp_face = mp.solutions.face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=settings.face_detection_confidence
            )
            logger.info("MediaPipe face detection initialized")
        except Exception as e:
            logger.warning(f"MediaPipe init failed, using OpenCV fallback: {e}")
            self.mp_face = None

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if self.mp_face:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.mp_face.process(rgb)
            faces = []
            if results.detections:
                h, w = frame.shape[:2]
                for det in results.detections:
                    bbox = det.location_data.relative_bounding_box
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    bw = int(bbox.width * w)
                    bh = int(bbox.height * h)
                    faces.append((x, y, bw, bh))
            return faces
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
            )
            return [(x, y, w, h) for (x, y, w, h) in faces]

    def get_crop_region(self, frame: np.ndarray, prev_center: Optional[Tuple[int, int]] = None) -> Tuple[int, int, int, int]:
        h, w = frame.shape[:2]
        target_w = settings.target_width
        target_h = settings.target_height

        if w / h > target_w / target_h:
            new_w = int(h * target_w / target_h)
            new_h = h
        else:
            new_w = w
            new_h = int(w * target_h / target_w)

        faces = self.detect_faces(frame)

        if faces:
            largest = max(faces, key=lambda f: f[2] * f[3])
            fx, fy, fw, fh = largest
            center_x = fx + fw // 2
            center_y = fy + fh // 2

            if prev_center:
                center_x = int(prev_center[0] * 0.7 + center_x * 0.3)
                center_y = int(prev_center[1] * 0.7 + center_y * 0.3)
        else:
            center_x = w // 2
            center_y = h // 2

        left = max(0, min(center_x - new_w // 2, w - new_w))
        top = max(0, min(center_y - new_h // 2, h - new_h))

        return (left, top, new_w, new_h)


class CaptionGenerator:
    @staticmethod
    def generate_ass(
        clip: ViralClip,
        words: List[dict],
        output_path: Path,
        font_size: int = None,
        font_color: str = None,
        highlight_color: str = None,
        outline_color: str = None,
        outline_width: int = None,
        margin_v: int = None
    ) -> Path:
        fs = font_size or settings.caption_font_size
        fc = font_color or settings.caption_color.replace('#', '')
        hc = highlight_color or settings.caption_highlight_color.replace('#', '')
        oc = outline_color or settings.caption_outline_color.replace('#', '')
        ow = outline_width or settings.caption_outline_width
        mv = margin_v or settings.caption_margin_v

        header = f"""[Script Info]
Title: {clip.title}
ScriptType: v4.00+
PlayResX: {settings.target_width}
PlayResY: {settings.target_height}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{settings.caption_font},{fs},&H{fc}&,&H{hc}&,&H{oc}&,&H00000000,-1,0,0,0,100,100,0,0,1,{ow},0,2,20,20,{mv},1
Style: Highlight,{settings.caption_font},{fs},&H{hc}&,&H{hc}&,&H{oc}&,&H00000000,-1,0,0,0,100,100,0,0,1,{ow},0,2,20,20,{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        for w in words:
            start = CaptionGenerator._format_time(w['start'] - clip.start_time)
            end = CaptionGenerator._format_time(w['end'] - clip.start_time)
            word = w['word'].strip()
            if word:
                events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{word}")

        highlight_events = []
        for i, w in enumerate(words):
            word = w['word'].strip()
            if not word:
                continue
            start = CaptionGenerator._format_time(w['start'] - clip.start_time)
            end = CaptionGenerator._format_time(w['end'] - clip.start_time)
            prefix = ''.join(w2['word'].strip() for w2 in words[:i] if w2['word'].strip())
            highlight_events.append(
                f"Dialogue: 1,{start},{end},Highlight,,0,0,0,{{\\t({{clip.start_time}})}},"  # placeholder
                # We'll use inline karaoke tags instead
            )

        # Build karaoke-style word-by-word highlighting
        karaoke_lines = CaptionGenerator._build_karaoke_lines(words, clip.start_time)

        content = header + "\n".join(karaoke_lines)
        output_path.write_text(content, encoding='utf-8-sig')
        return output_path

    @staticmethod
    def _format_time(seconds: float) -> str:
        if seconds < 0:
            seconds = 0
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds - int(seconds)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    @staticmethod
    def _build_karaoke_lines(words: List[dict], clip_start: float) -> List[str]:
        lines = []
        current_line_words = []
        current_line_start = None
        max_chars_per_line = 32
        line_char_count = 0

        def flush_line():
            nonlocal current_line_words, current_line_start, line_char_count
            if not current_line_words:
                return
            start_time = CaptionGenerator._format_time(current_line_words[0]['start'] - clip_start)
            end_time = CaptionGenerator._format_time(current_line_words[-1]['end'] - clip_start)
            karaoke_text = ""
            for w in current_line_words:
                word = w['word'].strip()
                if word:
                    dur = int((w['end'] - w['start']) * 100)
                    karaoke_text += f"{{\\k{dur}}}{word} "
            lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text.strip()}")
            current_line_words = []
            current_line_start = None
            line_char_count = 0

        for w in words:
            word = w['word'].strip()
            if not word:
                continue
            if current_line_start is None:
                current_line_start = w['start']
            current_line_words.append(w)
            line_char_count += len(word) + 1
            if line_char_count > max_chars_per_line:
                flush_line()

        flush_line()
        return lines


class VideoRenderer:
    def __init__(self):
        self.face_tracker = FaceTracker()

    def get_video_info(self, video_path: Path) -> dict:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }
        cap.release()
        return info

    def extract_audio(self, video_path: Path, output_path: Path) -> Path:
        cmd = [
            'ffmpeg', '-y', '-i', str(video_path),
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {result.stderr}")
        return output_path

    def render_clip(
        self,
        input_video: Path,
        clip: ViralClip,
        output_path: Path,
        ass_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Path:
        info = self.get_video_info(input_video)
        src_w, src_h = info['width'], info['height']
        dst_w, dst_h = settings.target_width, settings.target_height

        if progress_callback:
            progress_callback(10, "Analyzing video for crop regions...")

        crop_filters = self._compute_crop_filters(input_video, clip, src_w, src_h, dst_w, dst_h)

        if progress_callback:
            progress_callback(30, "Rendering video with captions...")

        filter_complex = (
            f"[0:v]{crop_filters},"
            f"subtitles={ass_path}:force_style='Fontsize={settings.caption_font_size}',"
            f"fps={settings.target_fps},"
            f"scale={dst_w}:{dst_h}:force_original_aspect_ratio=decrease,"
            f"pad={dst_w}:{dst_h}:(ow-iw)/2:(oh-ih)/2:color=black@0[v];"
            f"[0:a]anull[a]"
        )

        cmd = [
            'ffmpeg', '-y',
            '-ss', str(clip.start_time),
            '-t', str(clip.duration),
            '-i', str(input_video),
            '-filter_complex', filter_complex,
            '-map', '[v]', '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            str(output_path)
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if 'time=' in line and progress_callback:
                try:
                    time_str = line.split('time=')[1].split()[0]
                    h, m, s = time_str.split(':')
                    current_sec = int(h) * 3600 + int(m) * 60 + float(s)
                    pct = 30 + int((current_sec / clip.duration) * 65)
                    progress_callback(min(pct, 95), f"Rendering... {int(current_sec)}s / {int(clip.duration)}s")
                except:
                    pass

        process.wait()
        if process.returncode != 0:
            _, stderr = process.communicate()
            raise RuntimeError(f"FFmpeg render failed: {stderr}")

        if progress_callback:
            progress_callback(100, "Render complete")

        return output_path

    def _compute_crop_filters(
        self,
        video_path: Path,
        clip: ViralClip,
        src_w: int,
        src_h: int,
        dst_w: int,
        dst_h: int
    ) -> str:
        cap = cv2.VideoCapture(str(video_path))
        cap.set(cv2.CAP_PROP_POS_MSEC, clip.start_time * 1000)

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(clip.duration * fps)
        sample_every = max(1, total_frames // 30)

        crop_x = src_w // 2 - dst_w // 2
        crop_y = src_h // 2 - dst_h // 2
        crop_w = min(dst_w, src_w)
        crop_h = min(dst_h, src_h)

        if src_w / src_h > dst_w / dst_h:
            crop_w = int(src_h * dst_w / dst_h)
            crop_h = src_h
        else:
            crop_w = src_w
            crop_h = int(src_w * dst_h / dst_w)

        centers = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_every == 0:
                left, top, cw, ch = self.face_tracker.get_crop_region(frame)
                centers.append((left + cw // 2, top + ch // 2))
            frame_idx += 1
            if frame_idx >= total_frames:
                break

        cap.release()

        if centers:
            avg_x = sum(c[0] for c in centers) // len(centers)
            avg_y = sum(c[1] for c in centers) // len(centers)
            crop_x = max(0, min(avg_x - crop_w // 2, src_w - crop_w))
            crop_y = max(0, min(avg_y - crop_h // 2, src_h - crop_h))

        return f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"

    def render_all_clips(
        self,
        input_video: Path,
        clips: List[ViralClip],
        transcriptions: List[List[dict]],
        output_dir: Path,
        progress_callback: Optional[callable] = None
    ) -> List[Path]:
        output_files = []
        total = len(clips)

        for i, (clip, words) in enumerate(zip(clips, transcriptions)):
            if progress_callback:
                base = int((i / total) * 100)
                progress_callback(base, f"Rendering clip {i+1}/{total}: {clip.title}")

            clip_dir = output_dir / clip.id
            clip_dir.mkdir(parents=True, exist_ok=True)

            ass_path = clip_dir / f"{clip.id}.ass"
            CaptionGenerator.generate_ass(clip, words, ass_path)

            output_path = clip_dir / f"{clip.id}_{clip.title[:40]}.mp4"
            self.render_clip(
                input_video,
                clip,
                output_path,
                ass_path,
                lambda p, m: progress_callback(base + int(p * 0.9 / total), m) if progress_callback else None
            )

            output_files.append(output_path)

        return output_files