import React from "react";

/**
 * Language definitions.
 */
export const LANGUAGES = [
  { code: "te", native: "తెలుగు", english: "Telugu", flag: "🇮🇳" },
  { code: "hi", native: "हिंदी", english: "Hindi", flag: "🇮🇳" },
  { code: "kn", native: "ಕನ್ನಡ", english: "Kannada", flag: "🇮🇳" },
  { code: "ta", native: "தமிழ்", english: "Tamil", flag: "🇮🇳" },
];

/**
 * Sticky bottom pill bar for language selection.
 * Controlled component: value + onChange props, parent owns the state.
 */
export default function LanguagePicker({ value, onChange }) {
  return (
    <div className="sticky bottom-0 left-0 right-0 px-4 pb-5 pt-3 bg-gradient-to-t from-background via-background to-transparent">
      <div className="flex items-center justify-center gap-2 bg-surface rounded-full p-1.5 shadow-md">
        <span className="text-primary/50 text-sm pl-2 flex-shrink-0">🌐</span>

        {LANGUAGES.map((lang) => {
          const isSelected = value === lang.code;
          return (
            <button
              key={lang.code}
              id={`lang-${lang.code}`}
              onClick={() => onChange(lang.code)}
              className={`
                flex items-center gap-1 px-3 py-2 rounded-full text-sm font-semibold
                transition-all duration-200 whitespace-nowrap
                ${
                  isSelected
                    ? "bg-accent text-primary border-2 border-primary shadow-sm"
                    : "text-text/60 hover:text-text/80 hover:bg-surface-dark border-2 border-transparent"
                }
              `}
            >
              <span className="text-xs">{lang.flag}</span>
              <span>{lang.native}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
