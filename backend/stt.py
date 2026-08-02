"""
Speech-to-text using OpenAI's Whisper API (model="whisper-1").

The OpenAI client is created lazily INSIDE the transcribe function, not at
module import time, so the app doesn't crash on import if OPENAI_API_KEY is
temporarily missing.
"""

import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

_client = None


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


def transcribe(audio_bytes: bytes, lang: str = "hi") -> str:
    """
    Transcribe audio bytes to text using OpenAI/Groq Whisper.

    Args:
        audio_bytes: Raw bytes of the audio file (e.g. WebM).
        lang: Two-letter ISO language code used as a Whisper language hint.
              Whisper supports te, hi, kn, ta with the same codes directly.

    Returns:
        The transcribed text, stripped of whitespace.

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
            )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return response.text.strip()
