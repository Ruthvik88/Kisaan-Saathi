"""Tests for llm.parse_llm_output (no API calls)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import parse_llm_output


def test_valid_in_domain_json():
    out = parse_llm_output('{"intent": "in_domain", "reply": "आज मौसम साफ रहेगा।"}')
    assert out.intent == "in_domain"
    assert out.reply == "आज मौसम साफ रहेगा।"


def test_valid_ambiguous_json():
    out = parse_llm_output('{"intent": "ambiguous", "reply": "आप कौन सी फसल के बारे में पूछ रहे हैं?"}')
    assert out.intent == "ambiguous"
    assert "फसल" in out.reply


def test_valid_out_of_domain_json():
    out = parse_llm_output('{"intent": "out_of_domain", "reply": "मैं सिर्फ खेती के सवालों में मदद कर सकता हूँ।"}')
    assert out.intent == "out_of_domain"


def test_json_inside_code_fences():
    raw = '```json\n{"intent": "ambiguous", "reply": "कौन सी फसल?"}\n```'
    out = parse_llm_output(raw)
    assert out.intent == "ambiguous"
    assert out.reply == "कौन सी फसल?"


def test_json_inside_plain_fences():
    raw = '```\n{"intent": "out_of_domain", "reply": "खेती का सवाल पूछिए।"}\n```'
    out = parse_llm_output(raw)
    assert out.intent == "out_of_domain"


def test_malformed_output_falls_back_to_in_domain():
    raw = "Sorry, I could not format that as JSON but here is advice."
    out = parse_llm_output(raw)
    assert out.intent == "in_domain"
    assert out.reply == raw


def test_unknown_intent_falls_back_to_in_domain():
    out = parse_llm_output('{"intent": "something_else", "reply": "कुछ जवाब"}')
    assert out.intent == "in_domain"
    assert out.reply == "कुछ जवाब"


def test_empty_string_returns_empty_in_domain():
    out = parse_llm_output("")
    assert out.intent == "in_domain"
    assert out.reply == ""
