const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8422";

export interface Match {
  company: string;
  title: string;
  location: string;
  url: string;
  score: number;
  category: "strong" | "possible" | "poor";
  reasoning: string;
  draft?: string | null;
}

export interface ShortlistResult {
  matches: Match[];
  total_fetched: number;
  total_after_dedup: number;
  total_scored: number;
  trace_id: string;
  disclaimer: string;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function runShortlist(): Promise<ShortlistResult> {
  return fetch(`${API_BASE}/shortlist`, { method: "POST" }).then((res) => handle<ShortlistResult>(res));
}

export function fetchHealth(): Promise<{ status: string; seen_postings_count: number }> {
  return fetch(`${API_BASE}/health`).then((res) => handle(res));
}
