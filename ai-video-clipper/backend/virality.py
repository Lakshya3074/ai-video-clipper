import json
import logging
import re
from typing import List, Optional, Dict, Any
import httpx
from config import settings
from models import ViralClip, ViralityAnalysis, TranscriptionResult, Segment

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert viral content analyzer for short-form video (TikTok, Reels, Shorts).
Your task: Given a full transcript with word-level timestamps, identify the TOP 3-5 standalone viral clips (30-60 seconds each).

CRITERIA for viral clips:
1. STRONG HOOK in first 3 seconds (question, bold claim, shock, curiosity gap)
2. SELF-CONTAINED narrative (makes sense without context)
3. HIGH RETENTION structure: Hook → Story/Proof → Payoff/Cliffhanger
4. EMOTIONAL RESONANCE: surprise, inspiration, controversy, relatability, humor
5. SHAREABILITY: quotable moments, actionable advice, "wait what" factor

OUTPUT FORMAT: Strict JSON only. No markdown, no explanations.
{
  "clips": [
    {
      "title": "Catchy title under 60 chars",
      "hook_reasoning": "Why this goes viral: specific hook type, emotional trigger, retention mechanism",
      "virality_score": 85,
      "start_time": 12.5,
      "end_time": 58.3,
      "duration": 45.8,
      "transcript": "Exact transcript text for this clip"
    }
  ]
}

RULES:
- Clips must be 30-60 seconds
- No overlapping clips (pick best non-overlapping segments)
- Prioritize clips with complete thoughts/sentences
- Score 1-100 honestly (70+ = viral potential)
- Return 3-5 clips maximum"""

USER_PROMPT_TEMPLATE = """Full video transcript (duration: {duration:.1f}s):

{transcript}

Find the top 3-5 viral clips."""


class ViralityAnalyzer:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=120.0)
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    def _format_transcript(self, result: TranscriptionResult) -> str:
        lines = []
        for seg in result.segments:
            lines.append(f"[{seg.start:.1f}s - {seg.end:.1f}s] {seg.text}")
        return "\n".join(lines)

    def _build_prompt(self, result: TranscriptionResult) -> str:
        transcript_text = self._format_transcript(result)
        return USER_PROMPT_TEMPLATE.format(
            duration=result.duration,
            transcript=transcript_text
        )

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        text = response_text.strip()
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}, text: {text[:500]}")
            raise ValueError(f"Invalid JSON from LLM: {e}")

    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        client = await self._get_client()
        payload = {
            "model": settings.ollama_model,
            "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 2048
            }
        }
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return self._parse_json_response(data.get("response", ""))

    async def _call_openai_compatible(self, prompt: str) -> Dict[str, Any]:
        if not settings.openai_base_url or not settings.openai_api_key:
            raise ValueError("OpenAI-compatible endpoint not configured")

        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"}
        }
        response = await client.post(
            f"{settings.openai_base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return self._parse_json_response(content)

    async def analyze(
        self,
        transcription: TranscriptionResult,
        progress_callback: Optional[callable] = None
    ) -> ViralityAnalysis:
        if progress_callback:
            progress_callback(10, "Building analysis prompt...")

        prompt = self._build_prompt(transcription)

        if progress_callback:
            progress_callback(30, "Sending to LLM for viral analysis...")

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                if settings.llm_provider == "ollama":
                    result = await self._call_ollama(prompt)
                else:
                    result = await self._call_openai_compatible(prompt)

                clips_data = result.get("clips", [])

                if not clips_data:
                    raise ValueError("No clips returned from LLM")

                clips = []
                for clip_data in clips_data[:5]:
                    clip = ViralClip(
                        title=clip_data.get("title", "Untitled Clip"),
                        hook_reasoning=clip_data.get("hook_reasoning", ""),
                        virality_score=max(1, min(100, clip_data.get("virality_score", 50))),
                        start_time=max(0, clip_data.get("start_time", 0)),
                        end_time=clip_data.get("end_time", clip_data.get("start_time", 0) + 30),
                        duration=clip_data.get("duration", 30),
                        transcript=clip_data.get("transcript", "")
                    )
                    clip.duration = clip.end_time - clip.start_time
                    clips.append(clip)

                clips.sort(key=lambda c: c.virality_score, reverse=True)

                if progress_callback:
                    progress_callback(100, f"Analysis complete: {len(clips)} clips found")

                return ViralityAnalysis(clips=clips)

            except Exception as e:
                last_error = e
                logger.warning(f"LLM attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    if progress_callback:
                        progress_callback(30 + attempt * 10, f"Retrying... ({attempt + 1}/{max_retries})")
                    continue

        raise RuntimeError(f"LLM analysis failed after {max_retries} attempts: {last_error}")