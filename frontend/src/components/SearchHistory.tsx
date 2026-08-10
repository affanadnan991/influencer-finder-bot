"use client";

interface HistoryEntry {
  job_id: string;
  target: string;
  keywords: string[];
  status: string;
  result_count: number;
  created_at: string;
}

interface SearchHistoryProps {
  jobs: HistoryEntry[];
  onSelect: (jobId: string) => void;
  activeJobId: string | null;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const statusIcon: Record<string, { color: string; d: string }> = {
  completed: { color: "text-green-400", d: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" },
  running:   { color: "text-violet-400", d: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
  failed:    { color: "text-red-400", d: "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" },
  queued:    { color: "text-gray-500", d: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
};

export default function SearchHistory({ jobs, onSelect, activeJobId }: SearchHistoryProps) {
  if (jobs.length === 0) return null;

  return (
    <div className="animate-fade-in">
      <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
        Recent Searches
      </h3>
      <div className="space-y-1.5">
        {jobs.slice(0, 5).map((job) => {
          const si = statusIcon[job.status] || statusIcon.queued;
          const isActive = job.job_id === activeJobId;
          return (
            <button
              key={job.job_id}
              onClick={() => onSelect(job.job_id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg transition-all flex items-center gap-3 group ${
                isActive
                  ? "bg-violet-900/30 border border-violet-700/50"
                  : "bg-gray-800/40 border border-transparent hover:bg-gray-800 hover:border-gray-700"
              }`}
            >
              <svg className={`w-4 h-4 shrink-0 ${si.color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d={si.d} />
              </svg>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-white font-medium truncate">
                    @{job.target}
                  </span>
                  {job.result_count > 0 && (
                    <span className="text-xs text-green-400 tabular-nums shrink-0">
                      {job.result_count} found
                    </span>
                  )}
                </div>
                {job.keywords.length > 0 && (
                  <p className="text-xs text-gray-500 truncate">
                    {job.keywords.join(", ")}
                  </p>
                )}
              </div>
              <span className="text-[10px] text-gray-600 shrink-0">
                {timeAgo(job.created_at)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
