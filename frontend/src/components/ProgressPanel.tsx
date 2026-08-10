"use client";

import { useState, useEffect } from "react";
import type { JobStatus } from "@/lib/api";

interface ProgressPanelProps {
  status: JobStatus;
}

function useElapsed(startIso: string, running: boolean) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!running) return;
    const start = new Date(startIso).getTime();
    const tick = () => setElapsed(Math.floor((Date.now() - start) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startIso, running]);
  return elapsed;
}

function fmtTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}

export default function ProgressPanel({ status }: ProgressPanelProps) {
  const { counters, phase, detail } = status;
  const total = counters.followings_found || 0;
  const checked = counters.profiles_checked || 0;
  const pct = total > 0 ? Math.round((checked / total) * 100) : 0;
  const isRunning = status.status === "running";
  const elapsed = useElapsed(status.created_at, isRunning);

  const phaseConfig: Record<string, { label: string; icon: string }> = {
    starting:   { label: "Starting browser...", icon: "M12 6v6l4 2" },
    collecting: { label: "Collecting followings...", icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" },
    checking:   { label: "Checking profiles...", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" },
    done:       { label: "Done!", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" },
  };

  const cfg = phaseConfig[phase] || { label: phase || "Starting...", icon: "M12 6v6l4 2" };

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 space-y-4 animate-fade-in">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className={`w-4 h-4 ${isRunning ? "text-violet-400" : "text-green-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d={cfg.icon} />
          </svg>
          <h3 className="text-sm font-medium text-gray-200">{cfg.label}</h3>
        </div>
        <div className="flex items-center gap-3">
          {isRunning && (
            <span className="text-xs text-gray-500 tabular-nums">
              {fmtTime(elapsed)}
            </span>
          )}
          {status.status === "running" && (
            <span className="inline-flex items-center gap-1.5 text-xs text-green-400">
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
              Live
            </span>
          )}
          {status.status === "completed" && (
            <span className="inline-flex items-center gap-1.5 text-xs text-green-400">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Completed
            </span>
          )}
          {status.status === "failed" && (
            <span className="text-xs text-red-400">Failed</span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {total > 0 && (
        <div>
          <div className="flex justify-between text-xs text-gray-400 mb-1.5">
            <span>{checked} / {total} profiles</span>
            <span className="tabular-nums">{pct}%</span>
          </div>
          <div className="w-full h-2.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ease-out ${
                status.status === "completed"
                  ? "bg-green-500"
                  : "bg-gradient-to-r from-violet-600 to-violet-400 glow-pulse"
              }`}
              style={{ width: `${Math.max(pct, 2)}%` }}
            />
          </div>
        </div>
      )}

      {/* Detail text */}
      {detail && (
        <p className="text-xs text-gray-400 font-mono truncate">{detail}</p>
      )}

      {/* Counter cards */}
      <div className="grid grid-cols-4 gap-2 text-center">
        <CounterCard value={total} label="Found" color="text-blue-400" />
        <CounterCard value={counters.profiles_saved || 0} label="Matches" color="text-green-400" />
        <CounterCard value={checked} label="Checked" color="text-violet-400" />
        <CounterCard value={counters.profiles_skipped || 0} label="Skipped" color="text-gray-400" />
      </div>

      {/* Error */}
      {status.error && (
        <div className="flex items-start gap-2 bg-red-900/20 border border-red-800/50 rounded-lg p-3">
          <svg className="w-4 h-4 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.27 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <p className="text-sm text-red-300">{status.error}</p>
        </div>
      )}
    </div>
  );
}

function CounterCard({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <div className="bg-gray-900/60 rounded-lg py-2.5 px-1">
      <p className={`text-lg font-bold tabular-nums ${color}`}>{value}</p>
      <p className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</p>
    </div>
  );
}
