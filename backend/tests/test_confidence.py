"""Tests for confidence.assess_transcription (no API calls)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stt import TranscriptionResult
from confidence import assess_transcription


def _result(text, **kwargs):
    base = dict(
        avg_logprob=-0.3,
        max_no_speech_prob=0.1,
        max_compression_ratio=1.2,
        duration=3.0,
        segment_count=2,
        metrics_available=True,
    )
    base.update(kwargs)
    return TranscriptionResult(text=text, **base)


def test_reliable_transcript():
    a = assess_transcription(_result("आज मौसम कैसा रहेगा?"))
    assert a.reliable is True
    assert a.reason is None


def test_low_logprob_flagged():
    a = assess_transcription(_result("आज मौसम कैसा रहेगा?", avg_logprob=-1.5))
    assert a.reliable is False
    assert a.reason == "low_avg_logprob"


def test_high_no_speech_prob_flagged():
    a = assess_transcription(
        _result("आज मौसम कैसा रहेगा?", max_no_speech_prob=0.8)
    )
    assert a.reliable is False
    assert a.reason == "high_no_speech_prob"


def test_high_compression_ratio_flagged():
    a = assess_transcription(
        _result("मौसम मौसम मौसम मौसम", max_compression_ratio=3.0)
    )
    assert a.reliable is False
    assert a.reason == "high_compression_ratio"


def test_too_short_flagged():
    a = assess_transcription(_result("अ?"))
    assert a.reliable is False
    assert a.reason == "too_short"


def test_empty_flagged():
    a = assess_transcription(_result("   ... ??? "))
    assert a.reliable is False
    assert a.reason == "empty"


def test_missing_metrics_never_flags_on_metrics():
    # No segment data: even an odd-looking transcript passes the metric
    # gate; only the text-length check applies.
    a = assess_transcription(
        _result("आज मौसम कैसा रहेगा?", metrics_available=False,
                avg_logprob=None, max_no_speech_prob=None,
                max_compression_ratio=None)
    )
    assert a.reliable is True
    assert a.reason is None


def test_missing_metrics_still_flags_empty():
    a = assess_transcription(
        _result("", metrics_available=False, avg_logprob=None,
                max_no_speech_prob=None, max_compression_ratio=None)
    )
    assert a.reliable is False
    assert a.reason == "empty"


def test_threshold_overridable_via_env(monkeypatch):
    # With a stricter-tolerance threshold, a -1.5 logprob passes.
    monkeypatch.setenv("LOGPROB_THRESHOLD", "-2.0")
    a = assess_transcription(_result("आज मौसम कैसा रहेगा?", avg_logprob=-1.5))
    assert a.reliable is True
