"use client";

import { useState, useEffect, useCallback } from "react";
import SearchForm from "@/components/SearchForm";
import ProgressPanel from "@/components/ProgressPanel";
import ResultsTable from "@/components/ResultsTable";
import SearchHistory from "@/components/SearchHistory";
import { useJobProgress } from "@/lib/useJobProgress";
import {
  startSearch,
  getResults,
  getDownloadUrl,
  type ProfileResult,
  type JobStatus,
} from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [results, setResults] = useState<ProfileResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);

  // WebSocket-driven progress
  const { status, connected } = useJobProgress(isLoading ? jobId : null);

  // Load history
  const refreshHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/jobs`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.jobs.reverse());
      }
    } catch {}
  }, []);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  const handleSearch = async (
    target: string,
    keywords: string[],
    maxFollowing: number
  ) => {
    setError(null);
    setResults([]);
    setIsLoading(true);

    try {
      const res = await startSearch({
        target,
        keywords,
        max_following: maxFollowing,
      });
      setJobId(res.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search start failed");
      setIsLoading(false);
    }
  };

  // When job finishes, fetch results + refresh history
  useEffect(() => {
    if (!status || !jobId) return;

    if (status.status === "completed") {
      setIsLoading(false);
      getResults(jobId)
        .then((r) => setResults(r.results))
        .catch(() => {});
      refreshHistory();
    } else if (status.status === "failed") {
      setIsLoading(false);
      setError(status.error || "Job failed");
      refreshHistory();
    }
  }, [status?.status, jobId, refreshHistory]);

  // Load a past job from history
  const handleHistorySelect = async (selectedJobId: string) => {
    setJobId(selectedJobId);
    setError(null);
    setIsLoading(false);
    try {
      const res = await fetch(`${API_BASE}/api/status/${selectedJobId}`);
      if (!res.ok) return;
      const statusData: JobStatus = await res.json();

      // If completed, load results
      if (statusData.status === "completed") {
        try {
          const r = await getResults(selectedJobId);
          setResults(r.results);
        } catch {
          setResults([]);
        }
      } else {
        setResults([]);
      }
    } catch {}
  };

  const isDone = status?.status === "completed";
  const matchCount = status?.counters?.profiles_saved || 0;

  return (
    <main className="min-h-screen flex flex-col bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800/80 bg-gray-900/60 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-violet-600/20">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Influencer Finder</h1>
              <p className="text-xs text-gray-500">Instagram followings se relevant profiles dhundho</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {isLoading && connected && (
              <span className="inline-flex items-center gap-1.5 text-xs text-green-400 bg-green-900/20 px-2.5 py-1 rounded-full border border-green-800/30">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                Live
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 max-w-4xl mx-auto w-full px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column — form + history */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <SearchForm onSubmit={handleSearch} isLoading={isLoading} />
            </div>

            {/* Search History */}
            {history.length > 0 && (
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                <SearchHistory
                  jobs={history}
                  onSelect={handleHistorySelect}
                  activeJobId={jobId}
                />
              </div>
            )}
          </div>

          {/* Right column — progress + results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Error */}
            {error && !status?.error && (
              <div className="flex items-start gap-2 bg-red-900/20 border border-red-800/50 rounded-xl p-4 animate-fade-in">
                <svg className="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.27 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <p className="text-sm text-red-300">{error}</p>
              </div>
            )}

            {/* Progress */}
            {status && <ProgressPanel status={status} />}

            {/* Completion Summary */}
            {isDone && jobId && (
              <div className="bg-gradient-to-r from-green-900/20 to-violet-900/20 border border-green-800/30 rounded-xl p-5 animate-fade-in">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-900/40 rounded-full flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">
                        Search complete for @{status.target}
                      </p>
                      <p className="text-xs text-gray-400">
                        {matchCount} {matchCount === 1 ? "profile" : "profiles"} matched out of{" "}
                        {status.counters.profiles_checked || 0} checked
                      </p>
                    </div>
                  </div>
                  {matchCount > 0 && (
                    <a
                      href={getDownloadUrl(jobId)}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-medium rounded-lg transition-colors shadow-md shadow-green-600/20"
                      download
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Download CSV
                    </a>
                  )}
                </div>
              </div>
            )}

            {/* Results */}
            {results.length > 0 && jobId && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <ResultsTable results={results} jobId={jobId} />
              </div>
            )}

            {/* Empty state */}
            {!status && !error && results.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
                <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h3 className="text-gray-400 font-medium mb-1">No search yet</h3>
                <p className="text-sm text-gray-600 max-w-xs">
                  Enter an Instagram username and keywords to find matching influencers from their followings.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-4 mt-auto">
        <p className="text-center text-xs text-gray-700">
          Influencer Finder &mdash; Next.js + FastAPI + WebSocket
        </p>
      </footer>
    </main>
  );
}
