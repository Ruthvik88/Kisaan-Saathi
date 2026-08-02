import React, { useRef, useCallback, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function VoiceRecorder({
  lang,
  pincode = "560001",
  isRecording,
  onRecordingStart,
  onRecordingStop,
  onProcessing,
  onResult,
  onError,
}) {
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const startTimeRef = useRef(null);
  const activeRef = useRef(false);
  const mimeTypeRef = useRef("");

  // ── FIX: keep latest callback props in refs so that stopRecording's
  // identity never changes, which prevents the useEffect from tearing
  // down and re-adding window-level pointerup/pointercancel listeners
  // every time App re-renders with new inline callback identities. ──
  const onRecordingStopRef = useRef(onRecordingStop);
  const onErrorRef = useRef(onError);
  const onRecordingStartRef = useRef(onRecordingStart);
  const onProcessingRef = useRef(onProcessing);
  const onResultRef = useRef(onResult);
  useEffect(() => {
    onRecordingStopRef.current = onRecordingStop;
    onErrorRef.current = onError;
    onRecordingStartRef.current = onRecordingStart;
    onProcessingRef.current = onProcessing;
    onResultRef.current = onResult;
  });

  const getSupportedMime = () => {
    const types = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/mp4",
    ];
    for (const t of types) {
      if (MediaRecorder.isTypeSupported(t)) return t;
    }
    return "";
  };

  const uploadAudio = useCallback(
    async (audioBlob) => {
      onProcessingRef.current();

      try {
        const formData = new FormData();
        formData.append("audio", audioBlob, "question.webm");
        formData.append("lang", lang);
        formData.append("pincode", pincode);

        const response = await fetch(`${API_URL}/ask`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          let detail = `Server error (${response.status})`;
          try {
            const errBody = await response.json();
            if (errBody.detail) detail = errBody.detail;
          } catch {
            // response wasn't JSON
          }
          onErrorRef.current(detail);
          return;
        }

        const transcriptB64 = response.headers.get("X-Transcript") || "";
        const answerB64 = response.headers.get("X-Answer") || "";

        const blob = await response.blob();
        const audioUrl = URL.createObjectURL(blob);

        onResultRef.current({ audioUrl, transcriptB64, answerB64 });
      } catch (err) {
        if (err.name === "TypeError") {
          onErrorRef.current(
            "Could not connect to the server. Check your internet connection and that the backend is running at " +
            API_URL
          );
        } else {
          onErrorRef.current(`Network error: ${err.message}`);
        }
      }
    },
    [lang, pincode]
  );

  // The ONE and ONLY place recorder.onstop is defined. Handles stopping
  // the mic stream, building the final blob, and uploading it.
  const finalizeRecording = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    if (chunksRef.current.length > 0) {
      const audioBlob = new Blob(chunksRef.current, {
        type: mimeTypeRef.current || "audio/webm",
      });
      chunksRef.current = [];

      if (audioBlob.size > 0) uploadAudio(audioBlob);
    }
  }, [uploadAudio]);

  // ── FIX: stopRecording now has NO callback-prop deps (uses refs
  // instead), so its identity is stable across App re-renders. ──
  const stopRecording = useCallback(() => {
    if (!activeRef.current) return;
    activeRef.current = false;

    // ── FIX: if startTimeRef.current is somehow null/0, treat elapsed
    // as Infinity (i.e. assume the recording was long enough) rather
    // than the old `|| Date.now()` which produced elapsed === 0. ──
    const now = Date.now();
    const elapsed = startTimeRef.current
      ? now - startTimeRef.current
      : Infinity;

    if (elapsed < 500) {
      // Stop the recorder but discard the result -- too short to be a
      // real question, likely an accidental tap.
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.onstop = null;
        mediaRecorderRef.current.ondataavailable = null;
        mediaRecorderRef.current.stop();
      }
      chunksRef.current = [];
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      onRecordingStopRef.current();
      onErrorRef.current(
        "Recording was too short — please hold the button and speak your question clearly."
      );
      return;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop(); // triggers finalizeRecording via onstop
    }

    onRecordingStopRef.current();
  }, []);  // ← stable: no deps that change across renders

  const startRecording = useCallback(async () => {
    if (activeRef.current) return;
    activeRef.current = true;
    startTimeRef.current = Date.now();
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // If the user released the button while we were asking for permissions,
      // clean up immediately and don't start recording.
      if (!activeRef.current) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      
      streamRef.current = stream;

      const mimeType = getSupportedMime();
      mimeTypeRef.current = mimeType;

      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined
      );
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = finalizeRecording;

      // Timeslice of 250ms: emits chunks periodically during recording
      // instead of relying on a single flush at stop time.
      recorder.start(250);
      onRecordingStartRef.current();
    } catch (err) {
      activeRef.current = false;
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        onErrorRef.current(
          "Microphone access was denied. Please allow microphone permission in your browser settings and try again."
        );
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        onErrorRef.current("No microphone found. Please connect a microphone and try again.");
      } else {
        onErrorRef.current(`Could not start recording: ${err.message}`);
      }
    }
  }, [finalizeRecording]);  // finalizeRecording is stable (deps: uploadAudio which only changes on lang/pincode)

  // ── FIX: since stopRecording now has a stable identity ([]),
  // this effect registers the listeners ONCE and never tears them
  // down / re-adds them during a recording session. ──
  useEffect(() => {
    const handleUp = (e) => {
      if (activeRef.current) stopRecording();
    };

    window.addEventListener("pointerup", handleUp);
    window.addEventListener("pointercancel", handleUp);

    return () => {
      window.removeEventListener("pointerup", handleUp);
      window.removeEventListener("pointercancel", handleUp);
    };
  }, [stopRecording]);

  // ── FIX: track the active pointerId to prevent duplicate
  // pointerdown from touch + mouse event coalescing ──
  const activePointerIdRef = useRef(null);

  const onPointerDown = (e) => {
    e.preventDefault();
    // If we already have an active pointer (or recording), ignore.
    if (activeRef.current) return;
    if (activePointerIdRef.current !== null) return;
    activePointerIdRef.current = e.pointerId;
    startRecording();
  };

  // Clear the active pointer on release so the next press works
  useEffect(() => {
    const clearPointerId = () => {
      activePointerIdRef.current = null;
    };
    window.addEventListener("pointerup", clearPointerId);
    window.addEventListener("pointercancel", clearPointerId);
    return () => {
      window.removeEventListener("pointerup", clearPointerId);
      window.removeEventListener("pointercancel", clearPointerId);
    };
  }, []);

  return (
    <button
      id="mic-record-button"
      onPointerDown={onPointerDown}
      onContextMenu={(e) => e.preventDefault()}
      onDragStart={(e) => e.preventDefault()}
      className={`
        w-44 h-44 sm:w-48 sm:h-48 rounded-full flex items-center justify-center
        select-none touch-none cursor-pointer transition-all duration-300 ease-out
        ${isRecording
          ? "bg-accent border-4 border-primary mic-glow-recording scale-95"
          : "bg-accent mic-glow hover:scale-105 active:scale-95 border-4 border-transparent"
        }
      `}
      aria-label="Hold to record"
    >
      <svg className="w-16 h-16 text-primary" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      </svg>
    </button>
  );
}