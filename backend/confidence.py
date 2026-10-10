"""
Pure transcription-reliability assessment.

assess_transcription() decides whether a Whisper transcript is reliable
enough to pass to generation. The metric thresholds mirror Whisper's own
decoding-failure heuristics:

- avg_logprob: mean token log-probability across segments. Very negative
  values mean the model was effectively guessing.
- no_speech_prob: high values mean the audio was mostly silence / non-speech.
- compression_ratio: high values mean repetitive, looped output — a classic
  Whisper hallucination signature (e.g. repeating one word for 30 seconds).

All thresholds are overridable via environment variables so they can be
calibrated on real Telugu, Hindi, Kannada and Tamil audio:

    LOGPROB_THRESHOLD      (default -1.0)
    NO_SPEECH_THRESHOLD    (default 0.6)
    COMPRESSION_THRESHOLD  (default 2.4)
    MIN_TRANSCRIPT_CHARS   (default 3)

This module is intentionally pure: no network, no disk, no API clients.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

DEFAULT_LOGPROB_THRESHOLD = -1.0
DEFAULT_NO_SPEECH_THRESHOLD = 0.6
DEFAULT_COMPRESSION_THRESHOLD = 2.4
DEFAULT_MIN_TRANSCRIPT_CHARS = 3


class Assessment:
    """Outcome of assess_transcription: reliable flag plus a reason code."""

    def __init__(self, reliable: bool, reason=None):
        self.reliable = reliable
        self.reason = reason

    def __repr__(self):  # pragma: no cover - debugging helper
        return f"Assessment(reliable={self.reliable}, reason={self.reason!r})"


def _get_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid %s=%r, using default %s", name, raw, default)
        return default


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid %s=%r, using default %s", name, raw, default)
        return default


def assess_transcription(result) -> Assessment:
    """
    Decide whether a TranscriptionResult is reliable enough for generation.

    Args:
        result: TranscriptionResult (or any object with .text,
                .avg_logprob, .max_no_speech_prob, .max_compression_ratio
                and .metrics_available attributes).

    Returns:
        Assessment(reliable=True, reason=None) when the transcript may be
        passed to generation, otherwise Assessment(reliable=False,
        reason=<one of "empty", "too_short", "low_avg_logprob",
        "high_no_speech_prob", "high_compression_ratio">).

    The raw metrics are logged at INFO on every call for threshold
    calibration. A transcript is NEVER flagged on metrics when
    metrics_available is False.
    """
    text = getattr(result, "text", "") or ""
    metrics_available = bool(getattr(result, "metrics_available", False))
    avg_logprob = getattr(result, "avg_logprob", None)
    max_no_speech_prob = getattr(result, "max_no_speech_prob", None)
    max_compression_ratio = getattr(result, "max_compression_ratio", None)

    logger.info(
        "STT metrics: text_len=%d metrics_available=%s avg_logprob=%s "
        "max_no_speech_prob=%s max_compression_ratio=%s "
        "duration=%s segment_count=%s",
        len(text),
        metrics_available,
        avg_logprob,
        max_no_speech_prob,
        max_compression_ratio,
        getattr(result, "duration", None),
        getattr(result, "segment_count", None),
    )

    # --- Text checks (always apply, even without metrics) ---
    # Strip punctuation/whitespace/symbols and count what remains, so that
    # transcripts like "..." or "??" don't pass on junk characters.
    # re.UNICODE keeps Indic-script letters as word characters.
    meaningful = re.sub(r"[\W_]+", "", text, flags=re.UNICODE)
    min_chars = _get_int_env("MIN_TRANSCRIPT_CHARS", DEFAULT_MIN_TRANSCRIPT_CHARS)
    if len(meaningful) == 0:
        return Assessment(reliable=False, reason="empty")
    if len(meaningful) < min_chars:
        return Assessment(reliable=False, reason="too_short")

    # --- Metric checks (only when the provider returned segment data) ---
    if metrics_available:
        logprob_threshold = _get_float_env(
            "LOGPROB_THRESHOLD", DEFAULT_LOGPROB_THRESHOLD
        )
        if avg_logprob is not None and avg_logprob < logprob_threshold:
            return Assessment(reliable=False, reason="low_avg_logprob")

        no_speech_threshold = _get_float_env(
            "NO_SPEECH_THRESHOLD", DEFAULT_NO_SPEECH_THRESHOLD
        )
        if (
            max_no_speech_prob is not None
            and max_no_speech_prob > no_speech_threshold
        ):
            return Assessment(reliable=False, reason="high_no_speech_prob")

        compression_threshold = _get_float_env(
            "COMPRESSION_THRESHOLD", DEFAULT_COMPRESSION_THRESHOLD
        )
        if (
            max_compression_ratio is not None
            and max_compression_ratio > compression_threshold
        ):
            return Assessment(reliable=False, reason="high_compression_ratio")

    return Assessment(reliable=True, reason=None)
