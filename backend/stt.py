"""
Speech-to-text using OpenAI's Whisper API (model="whisper-1") or Groq
(model="whisper-large-v3-turbo").

Requests response_format="verbose_json" so every transcription comes back
with per-segment decoding metrics (avg_logprob, no_speech_prob,
compression_ratio). confidence.py uses those metrics to detect unreliable
transcripts BEFORE they reach generation.

The OpenAI client is created lazily INSIDE transcribe, not at module import
time, so the app doesn't crash on import if OPENAI_API_KEY is temporarily
missing.
"""

import os
import tempfile
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

_client = None


@dataclass
class TranscriptionResult:
    """
    Transcript plus Whisper decoding metrics.

    avg_logprob is the mean of per-segment avg_logprob values (closer to 0
    is better; very negative means the model was guessing). max_no_speech_prob
    is the highest per-segment no_speech_prob (high means mostly silence or
    non-speech). max_compression_ratio is the highest per-segment
    compression_ratio (high means repetitive/looped output, a classic Whisper
    hallucination signal).

    When the provider response has no segment data, metrics_available is
    False and all metric fields stay None — callers must NEVER treat a
    transcript as unreliable based on metrics in that case.
    """

    text: str
    avg_logprob: float | None = None
    max_no_speech_prob: float | None = None
    max_compression_ratio: float | None = None
    duration: float | None = None
    segment_count: int = 0
    metrics_available: bool = False


def _get_client():
    """Lazily initialize and return the OpenAI client."""
    global _client
    if _client is None:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Add it to backend/.env or export it as an environment variable."
            )

        base_url = os.getenv("OPENAI_BASE_URL")
        if not base_url and api_key.startswith("gsk_"):
            base_url = "https://api.groq.com/openai/v1"

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        _client = OpenAI(**kwargs)
    return _client


def _seg_get(seg, *names):
    """Read a field from a segment that may be a dict or an object."""
    for name in names:
        if isinstance(seg, dict):
            if name in seg:
                return seg[name]
        elif hasattr(seg, name):
            return getattr(seg, name)
    return None


def _extract_metrics(response) -> TranscriptionResult:
    """Build a TranscriptionResult from a verbose_json Whisper response.

    Never crashes on missing/unexpected shapes — returns
    metrics_available=False when no usable segment data is present.
    """
    text = ""
    try:
        text = (getattr(response, "text", "") or "").strip()
    except Exception:
        text = ""

    segments = getattr(response, "segments", None)
    if not segments:
        return TranscriptionResult(text=text, metrics_available=False)

    try:
        segments = list(segments)
    except TypeError:
        return TranscriptionResult(text=text, metrics_available=False)

    if not segments:
        return TranscriptionResult(text=text, metrics_available=False)

    logprobs = []
    no_speech = []
    compressions = []
    for seg in segments:
        lp = _seg_get(seg, "avg_logprob")
        ns = _seg_get(seg, "no_speech_prob")
        cr = _seg_get(seg, "compression_ratio")
        if isinstance(lp, (int, float)):
            logprobs.append(float(lp))
        if isinstance(ns, (int, float)):
            no_speech.append(float(ns))
        if isinstance(cr, (int, float)):
            compressions.append(float(cr))

    if not logprobs and not no_speech and not compressions:
        return TranscriptionResult(
            text=text, segment_count=len(segments), metrics_available=False
        )

    duration = getattr(response, "duration", None)
    if not isinstance(duration, (int, float)):
        duration = None

    return TranscriptionResult(
        text=text,
        avg_logprob=(sum(logprobs) / len(logprobs)) if logprobs else None,
        max_no_speech_prob=max(no_speech) if no_speech else None,
        max_compression_ratio=max(compressions) if compressions else None,
        duration=float(duration) if duration is not None else None,
        segment_count=len(segments),
        metrics_available=True,
    )


def transcribe(audio_bytes: bytes, lang: str = "hi") -> TranscriptionResult:
    """
    Transcribe audio bytes to text using OpenAI/Groq Whisper.

    Args:
        audio_bytes: Raw bytes of the audio file (e.g. WebM).
        lang: Two-letter ISO language code used as a Whisper language hint.
              Whisper supports te, hi, kn, ta with the same codes directly.

    Returns:
        TranscriptionResult with the transcript text plus decoding metrics.

    Raises:
        Any exception from the API — intentionally not caught here.
    """
    client = _get_client()

    api_key = os.getenv("OPENAI_API_KEY", "")
    model = "whisper-large-v3-turbo" if api_key.startswith("gsk_") else "whisper-1"

    # Write bytes to a temporary file. Using .wav extension makes ffmpeg
    # probe the container and often bypasses WebM duration metadata issues
    # that Groq's backend sometimes struggles with.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=model,
                file=f,
                language=lang,
                response_format="verbose_json",
            )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return _extract_metrics(response)
