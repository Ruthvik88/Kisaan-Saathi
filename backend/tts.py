"""
Text-to-speech using gTTS (free, no API key required).

Synthesizes text into an in-memory MP3 buffer — never touches disk.
Raises on failure (does not swallow exceptions).
"""

import io
from gtts import gTTS


def synthesize(text: str, lang: str = "hi") -> io.BytesIO:
    """
    Convert text to speech audio (MP3).

    Args:
        text: The text to speak.
        lang: Two-letter code. gTTS supports te, hi, kn, ta directly.

    Returns:
        BytesIO buffer with MP3 audio, seeked to position 0.

    Raises:
        Any gTTS exception — intentionally not caught here.
    """
    tts = gTTS(text=text, lang=lang, slow=False)

    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    return audio_buffer
