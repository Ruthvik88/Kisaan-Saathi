import React, { useEffect, useRef, useState } from "react";

/**
 * Audio player card with play/pause, progress bar, and time labels.
 * Auto-plays when audioUrl changes (safe: always follows a user gesture).
 */
export default function AudioPlayer({ audioUrl }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [loading, setLoading] = useState(true);

  // Auto-play on URL change
  useEffect(() => {
    if (!audioUrl || !audioRef.current) return;
    setLoading(true);
    audioRef.current.src = audioUrl;
    audioRef.current
      .play()
      .then(() => { setPlaying(true); setLoading(false); })
      .catch(() => { setPlaying(false); setLoading(false); });

    return () => {
      if (audioRef.current) audioRef.current.pause();
    };
  }, [audioUrl]);

  const toggle = () => {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play().then(() => setPlaying(true));
    }
  };

  const onTimeUpdate = () => {
    if (audioRef.current) setCurrentTime(audioRef.current.currentTime);
  };

  const onLoaded = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
      setLoading(false);
    }
  };

  const onEnded = () => { setPlaying(false); setCurrentTime(0); };

  const seekTo = (e) => {
    if (!audioRef.current || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    audioRef.current.currentTime = ((e.clientX - rect.left) / rect.width) * duration;
  };

  const fmt = (s) => {
    const m = Math.floor(s / 60);
    const ss = Math.floor(s % 60);
    return `${m}:${ss.toString().padStart(2, "0")}`;
  };

  const pct = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm fade-in">
      <audio
        ref={audioRef}
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={onLoaded}
        onEnded={onEnded}
      />

      {/* Play / Pause button */}
      <div className="flex justify-center mb-5">
        <button
          id="audio-play-pause"
          onClick={toggle}
          disabled={loading}
          className="w-16 h-16 rounded-full bg-accent flex items-center justify-center
                     shadow-md hover:shadow-lg active:scale-95 transition-all duration-200
                     disabled:opacity-50"
        >
          {loading ? (
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          ) : playing ? (
            <svg className="w-7 h-7 text-primary" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : (
            <svg className="w-7 h-7 text-primary ml-1" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
      </div>

      {/* Progress bar */}
      <div className="progress-track cursor-pointer mb-2" onClick={seekTo}>
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>

      {/* Time labels */}
      <div className="flex justify-between text-xs text-text/40 font-medium">
        <span>{fmt(currentTime)}</span>
        <span>{fmt(duration)}</span>
      </div>
    </div>
  );
}
