"use client";

import { useState, useRef } from "react";

interface SearchFormProps {
  onSubmit: (target: string, keywords: string[], maxFollowing: number) => void;
  isLoading: boolean;
}

export default function SearchForm({ onSubmit, isLoading }: SearchFormProps) {
  const [target, setTarget] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [kwInput, setKwInput] = useState("");
  const [maxFollowing, setMaxFollowing] = useState(200);
  const kwRef = useRef<HTMLInputElement>(null);

  const addKeyword = (raw: string) => {
    const kw = raw.trim().toLowerCase();
    if (!kw || keywords.length >= 7 || keywords.includes(kw)) return;
    setKeywords((prev) => [...prev, kw]);
    setKwInput("");
  };

  const removeKeyword = (idx: number) => {
    setKeywords((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleKwKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addKeyword(kwInput);
    }
    if (e.key === "Backspace" && !kwInput && keywords.length > 0) {
      removeKeyword(keywords.length - 1);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim()) return;
    // Add any pending keyword input
    const finalKw = [...keywords];
    if (kwInput.trim()) {
      const pending = kwInput.trim().toLowerCase();
      if (!finalKw.includes(pending)) finalKw.push(pending);
    }
    onSubmit(target.trim().replace("@", ""), finalKw.slice(0, 7), maxFollowing);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Target Username */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          Target Instagram Username
        </label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 select-none">
            @
          </span>
          <input
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="nike"
            disabled={isLoading}
            autoFocus
            className="w-full pl-8 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent disabled:opacity-50 transition-shadow"
          />
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Jis profile ke followings check karne hain
        </p>
      </div>

      {/* Keywords with chips */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          Keywords
          <span className="text-gray-500 font-normal ml-1">
            (optional, {keywords.length}/7)
          </span>
        </label>
        <div
          className={`flex flex-wrap gap-1.5 p-2 bg-gray-800 border rounded-lg min-h-[42px] cursor-text transition-shadow ${
            isLoading
              ? "border-gray-700 opacity-50"
              : "border-gray-700 focus-within:ring-2 focus-within:ring-violet-500 focus-within:border-transparent"
          }`}
          onClick={() => kwRef.current?.focus()}
        >
          {keywords.map((kw, i) => (
            <span
              key={kw}
              className="inline-flex items-center gap-1 px-2.5 py-1 bg-violet-900/50 text-violet-300 text-xs rounded-full animate-fade-in"
            >
              {kw}
              {!isLoading && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeKeyword(i);
                  }}
                  className="hover:text-white transition-colors ml-0.5"
                >
                  &times;
                </button>
              )}
            </span>
          ))}
          <input
            ref={kwRef}
            type="text"
            value={kwInput}
            onChange={(e) => setKwInput(e.target.value)}
            onKeyDown={handleKwKeyDown}
            onBlur={() => { if (kwInput.trim()) addKeyword(kwInput); }}
            placeholder={keywords.length === 0 ? "fitness, gym, workout..." : keywords.length < 7 ? "add more..." : ""}
            disabled={isLoading || keywords.length >= 7}
            className="flex-1 min-w-[100px] bg-transparent border-none outline-none text-white text-sm placeholder-gray-500 disabled:cursor-not-allowed"
          />
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Type and press Enter to add. Bio mein match hone chahiye. Blank = collect all.
        </p>
      </div>

      {/* Max Following */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          Max Followings to Check
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={10}
            max={1000}
            step={10}
            value={maxFollowing}
            onChange={(e) => setMaxFollowing(Number(e.target.value))}
            disabled={isLoading}
            className="flex-1 h-2 bg-gray-700 rounded-full appearance-none cursor-pointer accent-violet-500 disabled:opacity-50"
          />
          <input
            type="number"
            value={maxFollowing}
            onChange={(e) =>
              setMaxFollowing(Math.min(1000, Math.max(1, Number(e.target.value))))
            }
            min={1}
            max={1000}
            disabled={isLoading}
            className="w-20 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm text-center focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50 tabular-nums"
          />
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={isLoading || !target.trim()}
        className="w-full py-3 px-4 bg-violet-600 hover:bg-violet-500 active:bg-violet-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-violet-600/20 hover:shadow-violet-500/30 disabled:shadow-none"
      >
        {isLoading ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Searching...
          </>
        ) : (
          <>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Start Search
          </>
        )}
      </button>
    </form>
  );
}
