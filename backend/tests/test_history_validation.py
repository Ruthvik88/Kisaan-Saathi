"""Tests for main.validate_history (no API calls, no server)."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import validate_history


def _entry(role="user", text="test question"):
    return {"role": role, "text": text}


def test_empty_and_none_history():
    assert validate_history(None) == []
    assert validate_history("") == []
    assert validate_history("[]") == []


def test_valid_history_passes_through():
    h = json.dumps([_entry("user", "मौसम कैसा है?"),
                    _entry("assistant", "मौसम साफ है।")])
    out = validate_history(h)
    assert out == [{"role": "user", "text": "मौसम कैसा है?"},
                   {"role": "assistant", "text": "मौसम साफ है।"}]


def test_too_many_entries_keeps_most_recent_six():
    h = json.dumps([_entry("user", f"q{i}") for i in range(8)])
    out = validate_history(h)
    assert len(out) == 6
    assert out[0]["text"] == "q2"
    assert out[-1]["text"] == "q7"


def test_bad_roles_dropped():
    h = json.dumps([_entry("user", "ok"),
                    _entry("system", "ignore me"),
                    {"role": "admin", "text": "x"},
                    {"role": "user", "text": "also ok"}])
    out = validate_history(h)
    assert out == [{"role": "user", "text": "ok"},
                   {"role": "user", "text": "also ok"}]


def test_long_text_truncated_to_500_chars():
    h = json.dumps([_entry("user", "अ" * 600)])
    out = validate_history(h)
    assert len(out) == 1
    assert len(out[0]["text"]) == 500


def test_malformed_json_ignored():
    assert validate_history("{not json") == []
    assert validate_history("just a string") == []


def test_non_list_json_ignored():
    assert validate_history(json.dumps({"role": "user"})) == []
    assert validate_history(json.dumps("hello")) == []


def test_non_dict_entries_dropped():
    h = json.dumps([_entry("user", "ok"), "junk", 42, None])
    out = validate_history(h)
    assert out == [{"role": "user", "text": "ok"}]
