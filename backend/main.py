"""
FastAPI backend for Kisaan Saathi voice assistant.

POST /ask flow:
  1. Receive audio (webm) + lang + pincode via multipart form
  2. Transcribe with Whisper (stt.py)
  3. Build weather+MSP context (context.py)
  4. Get Gemini answer (llm.py)
  5. Synthesize to speech (tts.py)
  6. Return audio/mpeg stream with base64-encoded transcript/answer headers

Error handling rule: STT/LLM/TTS failures raise HTTPException(502), they do
NOT return a fake "sorry" message with 200 OK. The frontend must be able to
distinguish real answers from failures.
"""

import base64
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kisaan Saathi API", version="1.0.0")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # expose_headers is REQUIRED — without it the browser's fetch() will
    # silently hide X-Transcript and X-Answer from JavaScript even though
    # the server sends them.
    expose_headers=["X-Transcript", "X-Answer"],
)

VALID_LANGS = {"te", "hi", "kn", "ta"}
MAX_AUDIO_SIZE = 15 * 1024 * 1024  # 15 MB


@app.get("/")
def root():
    return {"status": "ok", "service": "Kisaan Saathi API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/ask")
async def ask_endpoint(
    audio: UploadFile = File(...),
    lang: str = Form(...),
    pincode: str = Form("560001"),
):
    # --- Validate language ---
    if lang not in VALID_LANGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language '{lang}'. Must be one of: {', '.join(sorted(VALID_LANGS))}",
        )

    # --- Read and validate audio ---
    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large ({len(audio_bytes)} bytes). Max is 15 MB.",
        )

    # --- Step 1: Speech-to-text ---
    try:
        from stt import transcribe

        transcript = transcribe(audio_bytes, lang=lang)
    except Exception as exc:
        logger.error("STT failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Speech-to-text failed: {exc}")

    if not transcript.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not understand the recording. Please try speaking again, louder and closer to the mic.",
        )

    logger.info("Transcript (%s): %.100s", lang, transcript)

    # --- Step 2: Build context ---
    from context import build_context_string

    context_block = build_context_string()

    # --- Step 3: Get LLM answer ---
    try:
        from llm import ask as llm_ask

        answer = llm_ask(question=transcript, lang=lang, context_block=context_block)
    except Exception as exc:
        logger.error("LLM failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"AI answer generation failed: {exc}")

    logger.info("Answer (%s): %.100s", lang, answer)

    # --- Step 4: Text-to-speech ---
    try:
        from tts import synthesize

        audio_buffer = synthesize(text=answer, lang=lang)
    except Exception as exc:
        logger.error("TTS failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Text-to-speech failed: {exc}")

    # --- Build response ---
    # CRITICAL: HTTP headers only support Latin-1. Telugu/Hindi/Kannada/Tamil
    # text is NOT Latin-1 safe. We base64-encode the UTF-8 bytes before
    # setting them as header values.
    #
    # The frontend (TranscriptView.jsx) decodes via atob() -> Uint8Array ->
    # TextDecoder("utf-8"). Both sides MUST use base64 — do NOT switch to
    # urllib.parse.quote or any other encoding without updating the frontend
    # to match, or transcripts will render as garbage.
    transcript_b64 = base64.b64encode(transcript.encode("utf-8")).decode("ascii")
    answer_b64 = base64.b64encode(answer.encode("utf-8")).decode("ascii")

    return StreamingResponse(
        audio_buffer,
        media_type="audio/mpeg",
        headers={
            "X-Transcript": transcript_b64,
            "X-Answer": answer_b64,
        },
    )
