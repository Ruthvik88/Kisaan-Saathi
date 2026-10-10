# 🚜 Kisaan Saathi — किसान साथी

**Regional Language Voice Assistant for Indian Farmers.**

A voice-in, voice-out web app. Farmers pick their language (Telugu, Hindi,
Kannada, or Tamil), hold a button, ask a question out loud, and hear a short
spoken answer grounded in live weather data and government crop price
information.

## Core Features

1. **Crop Advisory** — sowing time, fertilizer/irrigation guidance, crop
   selection advice, grounded with live weather data.
2. **Disease / Pest Diagnosis** — general safe first-step guidance only,
   with mandatory referral to the local KVK (Krishi Vigyan Kendra) for
   confirmation. Never recommends specific pesticide brands or dosages.
3. **Weather Updates** — live temperature, humidity, rainfall, and rain
   probability from Open-Meteo, referenced naturally in answers.
4. **MSP Information** — Minimum Support Price data from a bundled JSON
   file, with reminders to verify at the local mandi.

## Project Structure

```
Kisaan Saathi/
├── backend/
│   ├── main.py            FastAPI app (POST /ask)
│   ├── stt.py             Whisper STT (OpenAI API)
│   ├── llm.py             Gemini LLM (gemini-2.5-flash)
│   ├── tts.py             gTTS text-to-speech
│   ├── context.py         Open-Meteo weather + MSP data
│   ├── msp_data.json      Hardcoded MSP reference prices
│   ├── requirements.txt   Pinned Python deps
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx            State machine (5 screens)
│   │   ├── VoiceRecorder.jsx  Hold-to-record
│   │   ├── LanguagePicker.jsx Bottom pill bar
│   │   ├── AudioPlayer.jsx    Play/pause + progress
│   │   ├── TranscriptView.jsx Base64 decode + cards
│   │   ├── main.jsx
│   │   └── index.css
│   ├── public/icons/      (add PWA icons manually)
│   ├── index.html
│   ├── package.json       Pinned JS deps
│   ├── vite.config.js     Vite 5 + PWA
│   ├── tailwind.config.js Design tokens
│   ├── postcss.config.js
│   └── .env.example
├── .gitignore
└── README.md
```

## Setup

### 1. Get API Keys

- **OpenAI API Key** (Whisper STT): https://platform.openai.com/api-keys
- **Google Gemini API Key** (LLM): https://aistudio.google.com/app/apikey

### 2. Create `.env` Files

**Backend:**
```bash
cd backend
cp .env.example .env
# Edit .env and add your real keys
```

**Frontend:**
```bash
cd frontend
cp .env.example .env
# Default VITE_API_URL=http://localhost:8000 is fine for local dev
```

### 3. Install Dependencies

**Backend:**
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 4. Run Dev Servers

**Backend** (terminal 1):
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Frontend** (terminal 2):
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

### 5. PWA Preview (production build)

PWA features don't activate under `npm run dev`. To test:
```bash
cd frontend
npm run build
npm run preview
```

## Deployment

### Backend — Render (Web Service)

| Setting | Value |
|---|---|
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"` |
| **PYTHON_VERSION** | `3.13.0` (any 3.12+ works) |

`--proxy-headers` is required so the app sees the real client IP from
Render's proxy (used by `/ask` rate limiting) instead of the proxy's IP.

**Environment variables** (Render Dashboard → Environment):

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Whisper STT (or Groq key starting with `gsk_`) |
| `OPENAI_BASE_URL` | Only for custom endpoints | Defaults to Groq when the key starts with `gsk_` |
| `GEMINI_API_KEY` | Yes | Gemini LLM |
| `ALLOWED_ORIGINS` | Yes (production) | Comma-separated frontend origin(s), e.g. `https://kisaan-saathi.vercel.app` (no trailing slash). Default: `http://localhost:5173,http://127.0.0.1:5173` |
| `RATE_LIMIT_ASK` | No | Per-IP limit for `POST /ask`, e.g. `10/minute` (default) |
| `MAX_CLARIFY_TURNS` | No | Clarification rounds before a final answer (default `2`) |
| `LOGPROB_THRESHOLD` / `NO_SPEECH_THRESHOLD` / `COMPRESSION_THRESHOLD` / `MIN_TRANSCRIPT_CHARS` | No | STT reliability tuning (defaults `-1.0` / `0.6` / `2.4` / `3`) |

`GET /health` is intentionally NOT rate limited — point Render's health
check (and any uptime monitor) at `/health`.

### Frontend — Vercel

| Setting | Value |
|---|---|
| **Root Directory** | `frontend` |
| **Framework Preset** | Vite |
| **Build Command** | `npm run build` (default) |
| **Environment variable** | `VITE_API_URL=https://<your-render-service>.onrender.com` |

After deploying the frontend, copy its `https://...vercel.app` URL into the
backend's `ALLOWED_ORIGINS` on Render and redeploy the backend.

## Troubleshooting

| Problem | Fix |
|---|---|
| **CORS errors in console** | Ensure frontend runs at `http://localhost:5173` (not 127.0.0.1 or other port). Backend CORS allows both localhost and 127.0.0.1 on port 5173. |
| **Mic not working** | Use `http://localhost:5173`, not `http://127.0.0.1:5173`. `getUserMedia` requires a secure context; `localhost` qualifies but raw IPs may not. Also check browser mic permissions. |
| **gTTS errors** | gTTS calls Google Translate servers — it requires internet access and won't work offline. |
| **Gemini 404 "model not found"** | Gemini model names get deprecated periodically. Check https://ai.google.dev/gemini-api/docs/models for current model names, then update `MODEL_NAME` in `backend/llm.py`. As of mid-2026, `gemini-2.5-flash` is the correct stable flash-tier model. |
| **`TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`** | `httpx` version is too new. Pin `httpx==0.27.2` (already in requirements.txt). Run `pip install httpx==0.27.2` if upgraded accidentally. |
| **Transcript shows as garbage/mojibake** | Backend base64-encodes UTF-8 headers; frontend decodes via `atob` → `Uint8Array` → `TextDecoder("utf-8")`. Both sides must match. |

## MSP Data Note

⚠️ `backend/msp_data.json` contains **illustrative reference MSP figures**
for the 2024-25 season. These are **not live prices**. Verify periodically
against the official CACP/PIB announcement for production use.

## License

Educational / demo project.
