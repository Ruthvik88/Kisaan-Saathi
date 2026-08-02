import React, { useState, useEffect, useRef } from "react";
import LanguagePicker, { LANGUAGES } from "./LanguagePicker.jsx";
import VoiceRecorder from "./VoiceRecorder.jsx";
import AudioPlayer from "./AudioPlayer.jsx";
import TranscriptView from "./TranscriptView.jsx";

const UI = {
  te: {
    subtitle: "మీ వ్యవసాయ సహాయకుడు",
    hold: "మాట్లాడటానికి నొక్కి పట్టుకోండి",
    holdEn: "Hold the button and speak",
    listening: "వింటున్నాము...",
    stopHint: "మాట్లాడటం ఆపివేసినప్పుడు రికార్డింగ్ ఆగిపోతుంది.",
    proc1: "సమాచారం సేకరిస్తున్నాము...",
    proc2: "వాతావరణం మరియు మంది ధరలు తెస్తున్నాము...",
    example: '"ఈ రోజు వాతావరణం ఎలా ఉంది?"',
    errTitle: "సంపర్కం విఫలమైంది",
    errDesc: "దయచేసి మీ ఇంటర్నెట్ కనెక్షన్ తనిఖీ చేసి మళ్ళీ ప్రయత్నించండి.",
    retry: "మళ్ళీ ప్రయత్నించండి",
    disclaimer: "మంది ధరలు అంచనా మాత్రమే. విక్రయం ముందు స్థానిక మంది వద్ద ధర నిర్ధారించుకోండి.",
  },
  hi: {
    subtitle: "आपका खेती सहायक",
    hold: "बोलने के लिए दबाकर रखें",
    holdEn: "Hold the button and speak",
    listening: "सुन रहे हैं...",
    stopHint: "बोलना बंद करने पर रिकॉर्डिंग रुक जाएगी।",
    proc1: "जानकारी जुटा रहे हैं...",
    proc2: "मौसम और मंडी के भाव ला रहे हैं...",
    example: '"आज मौसम कैसा रहेगा?"',
    errTitle: "संपर्क टूट गया है",
    errDesc: "कृपया अपना इंटरनेट कनेक्शन जाँचें और फिर से कोशिश करें.",
    retry: "पुनः प्रयास करें",
    disclaimer: "मंडी भाव अनुमानित हैं। बेचने से पहले अपनी स्थानीय मंडी से भाव की पुष्टि करें।",
  },
  kn: {
    subtitle: "ನಿಮ್ಮ ಕೃಷಿ ಸಹಾಯಕ",
    hold: "ಮಾತನಾಡಲು ಒತ್ತಿ ಹಿಡಿಯಿರಿ",
    holdEn: "Hold the button and speak",
    listening: "ಕೇಳುತ್ತಿದ್ದೇವೆ...",
    stopHint: "ಮಾತನಾಡುವುದನ್ನು ನಿಲ್ಲಿಸಿದಾಗ ರೆಕಾರ್ಡಿಂಗ್ ನಿಲ್ಲುತ್ತದೆ.",
    proc1: "ಮಾಹಿತಿ ಸಂಗ್ರಹಿಸುತ್ತಿದ್ದೇವೆ...",
    proc2: "ಹವಾಮಾನ ಮತ್ತು ಮಂಡಿ ಬೆಲೆಗಳನ್ನು ತರುತ್ತಿದ್ದೇವೆ...",
    example: '"ಇವತ್ತು ಹವಾಮಾನ ಹೇಗಿದೆ?"',
    errTitle: "ಸಂಪರ್ಕ ವಿಫಲವಾಗಿದೆ",
    errDesc: "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    retry: "ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ",
    disclaimer: "ಮಂಡಿ ಬೆಲೆಗಳು ಅಂದಾಜು ಮಾತ್ರ. ಮಾರಾಟ ಮಾಡುವ ಮೊದಲು ಸ್ಥಳೀಯ ಮಂಡಿಯಲ್ಲಿ ಬೆಲೆ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.",
  },
  ta: {
    subtitle: "உங்கள் விவசாய உதவியாளர்",
    hold: "பேச பொத்தானை அழுத்திப் பிடிக்கவும்",
    holdEn: "Hold the button and speak",
    listening: "கேட்டுக்கொண்டிருக்கிறோம்...",
    stopHint: "பேசுவதை நிறுத்தும்போது பதிவு நிற்கும்.",
    proc1: "தகவல் சேகரிக்கிறோம்...",
    proc2: "வானிலை மற்றும் மண்டி விலைகளை கொண்டுவருகிறோம்...",
    example: '"இன்று வானிலை எப்படி இருக்கும்?"',
    errTitle: "இணைப்பு துண்டிக்கப்பட்டது",
    errDesc: "உங்கள் இணைய இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
    retry: "மீண்டும் முயற்சிக்கவும்",
    disclaimer: "மண்டி விலைகள் தோராயமானவை. விற்பனை செய்வதற்கு முன் உள்ளூர் மண்டியில் விலையை உறுதிப்படுத்தவும்.",
  },
};

/* ────────────────────────────────────────────────────────────
   App component — single state machine
   ──────────────────────────────────────────────────────────── */
export default function App() {
  const [screen, setScreen] = useState("idle");
  const [lang, setLang] = useState("hi");
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef(null);

  const s = UI[lang];
  const langObj = LANGUAGES.find((l) => l.code === lang);

  // Recording timer
  useEffect(() => {
    if (screen === "recording") {
      setElapsed(0);
      timerRef.current = setInterval(() => setElapsed((p) => p + 1), 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [screen]);

  // Revoke old audio URL on new result
  useEffect(() => {
    return () => { if (result?.audioUrl) URL.revokeObjectURL(result.audioUrl); };
  }, [result]);

  const fmtTime = (sec) => `${Math.floor(sec / 60)}:${(sec % 60).toString().padStart(2, "0")}`;

  const onRecStart = () => setScreen("recording");
  const onRecStop = () => { };
  const onProcessing = () => setScreen("processing");
  const onResult = (data) => { setResult(data); setScreen("response"); };
  const onError = (msg) => { setErrorMsg(msg); setScreen("error"); };

  const reset = () => {
    if (result?.audioUrl) URL.revokeObjectURL(result.audioUrl);
    setResult(null);
    setErrorMsg("");
    setScreen("idle");
  };

  return (
    /* Full-viewport cream background */
    <div className="min-h-screen w-full bg-background font-body">
      {/* Centered phone frame */}
      <div className="max-w-[430px] mx-auto min-h-screen relative bg-background shadow-xl border-x border-surface-dark/30">

        {/* ═══════ IDLE & RECORDING (Always mounted, hidden if not active) ═══════ */}
        <div className={`flex flex-col min-h-screen fade-in ${screen === "idle" || screen === "recording" ? "" : "hidden"}`}>
          <header className="flex items-center justify-between px-5 pt-6 pb-2">
            <div>
              <h1 className="text-2xl font-extrabold text-primary flex items-center gap-2">
                <span>🚜</span><span>Kisaan Saathi</span>
              </h1>
              {screen === "idle" && <p className="text-sm text-text/50 font-medium mt-0.5">{s.subtitle}</p>}
            </div>
            {screen === "idle" && (
              <div className="flex items-center gap-1 bg-surface rounded-full px-3 py-1.5 text-sm font-semibold text-primary">
                <span>{langObj?.flag}</span><span>{langObj?.native}</span>
              </div>
            )}
          </header>

          <main className="flex-1 flex flex-col items-center justify-center px-5 pb-4">
            {screen === "recording" && (
              <>
                <p className="text-xl font-bold text-primary mb-1">{s.listening}</p>
                <p className="text-sm text-text/40 font-medium mb-6">{fmtTime(elapsed)}</p>
              </>
            )}

            <VoiceRecorder
              lang={lang} pincode="560001" isRecording={screen === "recording"}
              onRecordingStart={onRecStart} onRecordingStop={onRecStop}
              onProcessing={onProcessing} onResult={onResult} onError={onError}
            />

            {screen === "idle" && (
              <>
                <div className="mt-6 text-center">
                  <p className="text-lg font-bold text-text">{s.hold}</p>
                  <p className="text-sm text-text/40 mt-1">{s.holdEn}</p>
                </div>

                <div className="flex items-end gap-1 mt-5">
                  {[16, 24, 32, 40, 32, 24, 16, 24, 16].map((h, i) => (
                    <div key={i} className="w-1 rounded-full bg-primary/20" style={{ height: h }} />
                  ))}
                </div>

                <div className="mt-5 bg-surface rounded-full px-4 py-2.5 flex items-center gap-2 max-w-xs">
                  <span className="text-base flex-shrink-0">💡</span>
                  <p className="text-sm text-text/60 font-medium">{s.example}</p>
                </div>
              </>
            )}

            {screen === "recording" && (
              <>
                <div className="flex items-center gap-1.5 mt-8 h-12">
                  {Array.from({ length: 9 }).map((_, i) => (
                    <div key={i} className="wave-bar w-1.5 rounded-full bg-primary"
                      style={{ height: `${20 + Math.random() * 28}px` }} />
                  ))}
                </div>

                <div className="mt-6 bg-surface rounded-full px-4 py-2 max-w-xs">
                  <p className="text-xs text-text/40 text-center font-medium">{s.stopHint}</p>
                </div>
              </>
            )}
          </main>

          {screen === "idle" && <LanguagePicker value={lang} onChange={setLang} />}
        </div>

        {/* ═══════ PROCESSING ═══════ */}
        {screen === "processing" && (
          <div className="flex flex-col min-h-screen items-center justify-center px-5 fade-in">
            <div className="loading-ring w-28 h-28 flex items-center justify-center mb-6">
              <svg className="w-8 h-8 text-primary/60" fill="currentColor" viewBox="0 0 24 24">
                <rect x="3" y="9" width="2" height="6" rx="1" />
                <rect x="7" y="6" width="2" height="12" rx="1" />
                <rect x="11" y="4" width="2" height="16" rx="1" />
                <rect x="15" y="6" width="2" height="12" rx="1" />
                <rect x="19" y="9" width="2" height="6" rx="1" />
              </svg>
            </div>
            <p className="text-base font-semibold text-text/60 text-center">{s.proc1}</p>
            <p className="text-sm text-text/40 text-center mt-1">{s.proc2}</p>
          </div>
        )}

        {/* ═══════ RESPONSE ═══════ */}
        {screen === "response" && result && (
          <div className="flex flex-col min-h-screen fade-in">
            <header className="flex items-center px-5 pt-6 pb-3">
              <button id="back-button" onClick={reset}
                className="mr-3 w-9 h-9 rounded-full bg-surface flex items-center justify-center hover:bg-surface-dark transition-colors">
                <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-xl font-extrabold text-primary flex items-center gap-2">
                <span>🚜</span><span>Kisaan Saathi</span>
              </h1>
            </header>

            <main className="flex-1 px-5 pb-6 overflow-y-auto">
              <div className="mb-4">
                <AudioPlayer audioUrl={result.audioUrl} />
              </div>

              <div className="mb-5">
                <TranscriptView transcriptB64={result.transcriptB64} answerB64={result.answerB64} />
              </div>

              <button id="ask-another" onClick={reset}
                className="w-full bg-primary text-white font-bold text-base rounded-full py-4 flex items-center justify-center gap-2 hover:bg-primary/90 active:scale-[0.98] transition-all shadow-md">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
                Ask Another Question
              </button>

              <p className="text-xs text-text/35 text-center mt-4 px-4 leading-relaxed">{s.disclaimer}</p>
            </main>
          </div>
        )}

        {/* ═══════ ERROR ═══════ */}
        {screen === "error" && (
          <div className="flex flex-col min-h-screen fade-in">
            <header className="flex items-center justify-between px-5 pt-6 pb-2">
              <h1 className="text-2xl font-extrabold text-primary flex items-center gap-2">
                <span>🚜</span><span>Kisaan Saathi</span>
              </h1>
              <div className="flex items-center gap-1 bg-surface rounded-full px-3 py-1.5 text-sm font-semibold text-primary">
                <span>{langObj?.flag}</span><span>{langObj?.native}</span>
              </div>
            </header>

            <main className="flex-1 flex flex-col items-center justify-center px-6 pb-8">
              {/* Error icon with red glow */}
              <div className="relative mb-6">
                <div className="absolute inset-0 bg-red-100 rounded-3xl blur-xl opacity-60" />
                <div className="relative w-24 h-24 bg-white rounded-3xl shadow-sm flex items-center justify-center">
                  <svg className="w-12 h-12 text-primary" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round"
                      d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                </div>
              </div>

              <h2 className="text-xl font-bold text-text text-center mb-2">{s.errTitle}</h2>
              <p className="text-sm text-text/50 text-center mb-3 max-w-xs leading-relaxed">{s.errDesc}</p>

              <hr className="w-16 border-surface-dark mb-3" />

              <p className="text-xs text-text/35 text-center mb-6 max-w-xs leading-relaxed">
                {errorMsg || "Something went wrong. Please try again."}
              </p>

              <button id="retry-button" onClick={reset}
                className="w-full max-w-xs bg-primary text-white font-bold text-base rounded-full py-4 flex items-center justify-center gap-2 hover:bg-primary/90 active:scale-[0.98] transition-all shadow-md mb-3">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                </svg>
                {s.retry} / Try Again
              </button>

              <button id="go-back-link" onClick={reset}
                className="text-primary font-semibold text-sm hover:underline bg-transparent border-none cursor-pointer">
                Go Back
              </button>
            </main>
          </div>
        )}

      </div>
    </div>
  );
}
