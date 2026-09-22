const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SearchRequest {
  target: string;
  keywords: string[];
  max_following: number;
}

export interface SearchResponse {
  job_id: string;
  message: string;
}

export interface JobStatus {
  job_id: string;
  target: string;
  keywords: string[];
  status: "queued" | "running" | "completed" | "failed";
  phase: string;
  detail: string;
  counters: {
    followings_found: number;
    profiles_checked: number;
    keyword_matches: number;
    profiles_saved: number;
    profiles_skipped: number;
    bio_extract_failed: number;
    errors: number;
  };
  result_count: number;
  error: string;
  created_at: string;
  finished_at: string | null;
}

export interface ProfileResult {
  username: string;
  profile_url: string;
  niche: string;
  score: number;
  date_collected: string;
}

export interface ResultsResponse {
  job_id: string;
  status: string;
  result_count: number;
  results: ProfileResult[];
}

export async function startSearch(req: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    if (res.status === 409) {
      const data = await res.json().catch(() => null);
      throw new Error(data?.detail || "A search is already running. Wait for it to finish.");
    }
    throw new Error(`Search failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/api/status/${jobId}`);
  if (!res.ok) throw new Error(`Status check failed: ${res.statusText}`);
  return res.json();
}

export async function getResults(jobId: string): Promise<ResultsResponse> {
  // Works while the job is still running too — matched profiles are
  // returned as soon as they're found, not just after completion.
  const res = await fetch(`${API_BASE}/api/results/${jobId}`);
  if (!res.ok) throw new Error(`Results fetch failed: ${res.statusText}`);
  return res.json();
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/download/${jobId}`;
}
