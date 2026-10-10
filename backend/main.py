"""
FastAPI backend for Kisaan Saathi voice assistant.

POST /ask flow:
  1. Receive audio (webm) + lang + pincode + optional history/clarify_count
  2. Transcribe with Whisper verbose_json (stt.py) -> TranscriptionResult
  3. Assess reliability (confidence.py). If unreliable and under the clarify
     limit: SKIP the LLM, return a static localized "please repeat" message
     (clarify_messages.py) with X-Turn-Type=clarify,
     X-Clarify-Reason=low_confidence.
  4. Build weather+MSP context (context.py)
  5. Get Gemini intent + reply (llm.py), passing history as context data
  6. Map intent -> turn type: in_domain = "answer"; ambiguous/out_of_domain
     = "clarify" (under the limit) with matching reason
  7. Synthesize to speech (tts.py)
  8. Return audio/mpeg stream with base64-encoded transcript/answer headers
     plus X-Turn-Type ("answer" | "clarify") and, for clarify turns,
     X-Clarify-Reason ("low_confidence" | "ambiguous" | "out_of_domain")

The server is STATELESS: the client keeps the conversation and sends it
with each request as a JSON string. Unreliable transcripts are NEVER added
to history (the client is instructed to skip them too).

Error handling rule: STT/LLM/TTS failures raise HTTPException(502), they do
NOT return a fake "sorry" message with 200 OK. The frontend must be able to
distinguish real answers from failures.
"""

import base64
import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kisaan Saathi API", version="1.1.0")


def _parse_allowed_origins(raw: str | None) -> list:
    """Parse ALLOWED_ORIGINS (comma-separated) into a clean origin list."""
    if not raw:
        raw = "http://localhost:5173,http://127.0.0.1:5173"
    origins = []
    for entry in raw.split(","):
        entry = entry.strip().rstrip("/")
        if entry:
            origins.append(entry)
    if not origins:
        origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    return origins


ALLOWED_ORIGINS = _parse_allowed_origins(os.getenv("ALLOWED_ORIGINS"))
logger.info("CORS allowed origins: %s", ALLOWED_ORIGINS)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # expose_headers is REQUIRED — without it the browser's fetch() will
    # silently hide these headers from JavaScript even though the server
    # sends them.
    expose_headers=["X-Transcript", "X-Answer", "X-Turn-Type", "X-Clarify-Reason"],
)

# --- Rate limiting (POST /ask only; / and /health are NOT limited so Render
# and uptime monitors can ping /health freely). Client IP comes from the
# X-Forwarded-For header when uvicorn runs with --proxy-headers behind
# Render's proxy (see README Deployment section).
RATE_LIMIT_ASK = os.getenv("RATE_LIMIT_ASK", "10/minute")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please wait a minute and try again."},
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

VALID_LANGS = {"te", "hi", "kn", "ta"}
MAX_AUDIO_SIZE = 15 * 1024 * 1024  # 15 MB

# Max clarification rounds per conversation before we stop asking and give
# a final answer instead. Overridable via env for calibration.
MAX_CLARIFY_TURNS = int(os.getenv("MAX_CLARIFY_TURNS", "2"))

# History validation limits.
MAX_HISTORY_ENTRIES = 6
MAX_HISTORY_TEXT_CHARS = 500
VALID_HISTORY_ROLES = ("user", "assistant")


@app.get("/")
def root():
    return {"status": "ok", "service": "Kisaan Saathi API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


def validate_history(history_str) -> list:
    """
    Parse and sanitize the client-supplied conversation history.

    Returns a list of {"role": "user"/"assistant", "text": str} dicts.
    Invalid input NEVER raises: malformed JSON or a non-list is ignored
    entirely (warning logged); over-long lists keep the most recent 6;
    entries with bad roles/shapes are dropped; each text is truncated to
    500 chars.
    """
    if not history_str:
        return []
    try:
        data = json.loads(history_str)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Ignoring invalid history JSON: %s", exc)
        return []
    if not isinstance(data, list):
        logger.warning("Ignoring history: expected a JSON list, got %s", type(data).__name__)
        return []
    if len(data) > MAX_HISTORY_ENTRIES:
        logger.warning(
            "History has %d entries, keeping the most recent %d",
            len(data),
            MAX_HISTORY_ENTRIES,
        )
        data = data[-MAX_HISTORY_ENTRIES:]
    clean = []
    for entry in data:
        if not isinstance(entry, dict):
            logger.warning("Ignoring non-object history entry: %r", entry)
            continue
        role = entry.get("role")
        text = entry.get("text")
        if role not in VALID_HISTORY_ROLES or not isinstance(text, str):
            logger.warning("Ignoring history entry with bad role/text: %r", entry)
            continue
        clean.append({"role": role, "text": text[:MAX_HISTORY_TEXT_CHARS]})
    return clean


def _b64(text: str) -> str:
    # CRITICAL: HTTP headers only support Latin-1. Telugu/Hindi/Kannada/Tamil
    # text is NOT Latin-1 safe. We base64-encode the UTF-8 bytes before
    # setting them as header values.
    #
    # The frontend (TranscriptView.jsx) decodes via atob() -> Uint8Array ->
    # TextDecoder("utf-8"). Both sides MUST use base64 — do NOT switch to
    # urllib.parse.quote or any other encoding without updating the frontend
    # to match, or transcripts will render as garbage.
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _respond(transcript_text: str, spoken_text: str, lang: str,
             turn_type: str, clarify_reason: str | None = None):
    """Synthesize spoken_text and build the StreamingResponse with headers."""
    try:
        from tts import synthesize

        audio_buffer = synthesize(text=spoken_text, lang=lang)
    except Exception as exc:
        logger.error("TTS failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Text-to-speech failed: {exc}")

    headers = {
        "X-Transcript": _b64(transcript_text),
        "X-Answer": _b64(spoken_text),
        "X-Turn-Type": turn_type,
    }
    if turn_type == "clarify" and clarify_reason:
        headers["X-Clarify-Reason"] = clarify_reason

    return StreamingResponse(
        audio_buffer,
        media_type="audio/mpeg",
        headers=headers,
    )


@app.post("/ask")
@limiter.limit(RATE_LIMIT_ASK)
async def ask_endpoint(
    request: Request,
    audio: UploadFile = File(...),
    lang: str = Form(...),
    pincode: str = Form("560001"),
    history: str | None = Form(None),
    clarify_count: int = Form(0),
):
    # --- Validate language ---
    if lang not in VALID_LANGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language '{lang}'. Must be one of: {', '.join(sorted(VALID_LANGS))}",
        )

    # --- Clamp clarify_count into 0..5 ---
    try:
        clarify_count = int(clarify_count)
    except (TypeError, ValueError):
        clarify_count = 0
    clarify_count = max(0, min(5, clarify_count))

    # --- Validate history (never 500s on bad history) ---
    conversation = validate_history(history)

    # --- Read and validate audio ---
    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large ({len(audio_bytes)} bytes). Max is 15 MB.",
        )

    # --- Step 1: Speech-to-text (with confidence metrics) ---
    try:
        from stt import transcribe

        result = transcribe(audio_bytes, lang=lang)
    except Exception as exc:
        logger.error("STT failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Speech-to-text failed: {exc}")

    transcript = result.text or ""
    logger.info("Transcript (%s): %.100s", lang, transcript)

    # --- Step 2: Reliability gate — unreliable transcripts NEVER reach the LLM ---
    from confidence import assess_transcription

    assessment = assess_transcription(result)

    if not assessment.reliable:
        from clarify_messages import get_give_up_message, get_repeat_message

        logger.info(
            "Unreliable transcript (reason=%s, clarify_count=%d)",
            assessment.reason,
            clarify_count,
        )
        if clarify_count < MAX_CLARIFY_TURNS:
            repeat_text = get_repeat_message(lang, clarify_count)
            return _respond(
                transcript, repeat_text, lang,
                turn_type="clarify", clarify_reason="low_confidence",
            )
        # Limit reached: final polite message, no more questions.
        give_up_text = get_give_up_message(lang)
        return _respond(transcript, give_up_text, lang, turn_type="answer")

    # --- Step 3: Build context ---
    from context import build_context_string

    context_block = build_context_string()

    # --- Step 4: Get LLM intent + reply ---
    try:
        from llm import ask as llm_ask

        llm_result = llm_ask(
            question=transcript,
            lang=lang,
            context_block=context_block,
            history=conversation,
        )
    except Exception as exc:
        logger.error("LLM failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"AI answer generation failed: {exc}")

    logger.info(
        "LLM intent=%s (%s): %.100s", llm_result.intent, lang, llm_result.reply
    )

    # --- Step 5: Map intent -> turn type ---
    if llm_result.intent == "in_domain":
        return _respond(transcript, llm_result.reply, lang, turn_type="answer")

    if llm_result.intent in ("ambiguous", "out_of_domain"):
        if clarify_count < MAX_CLARIFY_TURNS:
            return _respond(
                transcript, llm_result.reply, lang,
                turn_type="clarify", clarify_reason=llm_result.intent,
            )
        # Limit reached.
        if llm_result.intent == "ambiguous":
            # One best-effort attempt: answer generally, stating assumptions.
            try:
                from llm import ask as llm_retry

                best = llm_retry(
                    question=transcript,
                    lang=lang,
                    context_block=context_block,
                    history=conversation,
                    best_effort=True,
                )
                return _respond(transcript, best.reply, lang, turn_type="answer")
            except Exception as exc:
                logger.error("LLM best-effort retry failed: %s", exc, exc_info=True)
                raise HTTPException(
                    status_code=502, detail=f"AI answer generation failed: {exc}"
                )
        # out_of_domain at the limit: return the redirect as a final answer.
        return _respond(transcript, llm_result.reply, lang, turn_type="answer")

    # Defensive: unknown intent (should not happen — llm.py normalizes).
    logger.warning("Unknown LLM intent %r, returning reply as answer", llm_result.intent)
    return _respond(transcript, llm_result.reply, lang, turn_type="answer")
