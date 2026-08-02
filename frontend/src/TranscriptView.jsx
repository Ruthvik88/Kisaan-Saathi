import React from "react";

/**
 * Decode a base64-encoded UTF-8 string to its original text.
 *
 * The backend base64-encodes UTF-8 bytes for X-Transcript / X-Answer
 * headers (HTTP headers only support Latin-1). Decoding steps:
 *   1. atob() -> binary string (one char per byte of UTF-8)
 *   2. Uint8Array.from() -> byte array
 *   3. TextDecoder("utf-8").decode() -> proper Unicode string
 *
 * Plain atob() output is Latin-1 code points, which corrupts multi-byte
 * UTF-8 (Indic scripts are 3 bytes/char). The TextDecoder step is essential.
 *
 * Exported for reusability and testability.
 */
export function decodeBase64Utf8(base64Str) {
  if (!base64Str) return "";
  const binaryStr = atob(base64Str);
  const bytes = Uint8Array.from(binaryStr, (ch) => ch.charCodeAt(0));
  return new TextDecoder("utf-8").decode(bytes);
}

/**
 * Renders the transcript and answer in styled cards.
 *
 * Props:
 *   - transcriptB64: raw base64-encoded UTF-8 string from X-Transcript
 *   - answerB64: raw base64-encoded UTF-8 string from X-Answer
 */
export default function TranscriptView({ transcriptB64, answerB64 }) {
  const transcript = decodeBase64Utf8(transcriptB64);
  const answer = decodeBase64Utf8(answerB64);

  if (!transcript && !answer) return null;

  return (
    <div className="w-full space-y-0 fade-in">
      {/* Transcript card */}
      <div className="bg-surface rounded-t-2xl px-5 py-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-6 h-6 rounded-full bg-surface-dark flex items-center justify-center text-xs">
            👤
          </span>
          <span className="text-xs font-bold text-text/50 uppercase tracking-wide">
            You asked
          </span>
        </div>
        <p className="text-text font-medium text-base leading-relaxed">
          &ldquo;{transcript}&rdquo;
        </p>
      </div>

      {/* Answer card */}
      <div className="bg-white rounded-b-2xl px-5 py-4 shadow-sm border-t border-surface-dark/50">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs">
            🌾
          </span>
          <span className="text-xs font-bold text-primary uppercase tracking-wide">
            Kisaan Saathi says
          </span>
        </div>
        <p className="text-text text-base leading-relaxed">{answer}</p>
      </div>
    </div>
  );
}
