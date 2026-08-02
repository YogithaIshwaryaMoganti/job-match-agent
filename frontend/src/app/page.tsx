"use client";

import { useState } from "react";
import styles from "./page.module.css";
import { Match, runShortlist, ShortlistResult } from "@/lib/api";

const CATEGORY_COLORS: Record<string, string> = {
  strong: "#3a8f5b",
  possible: "#c9971c",
  poor: "#8a8a92",
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ShortlistResult | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await runShortlist();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1 className={styles.title}>Job Match & Shortlist Agent</h1>
        <p className={styles.subtitle}>
          Fetches real, live postings from Greenhouse and Lever (public job-board APIs — no
          scraping), scores each against a candidate profile, and drafts a cover-letter
          opening for the strongest matches.
        </p>

        <div className={styles.profileCard}>
          <div className={styles.profileLabel}>Demo candidate profile</div>
          <div className={styles.profileHeadline}>Senior Software Engineer — Full-Stack & Agentic AI Systems</div>
          <div className={styles.profileSkills}>
            Java · Spring Boot · Python · FastAPI · Next.js · React · LLM APIs · Agentic tool-calling · RAG
          </div>
        </div>

        <button className={styles.button} onClick={run} disabled={loading}>
          {loading ? "Fetching postings and scoring…" : "Run shortlist"}
        </button>

        {error && <div className={styles.error}>{error}</div>}

        {result && (
          <>
            <div className={styles.disclaimer}>{result.disclaimer}</div>

            <div className={styles.statsRow}>
              <span>{result.total_fetched} postings fetched</span>
              <span>{result.total_after_dedup} new (after dedup)</span>
              <span>{result.total_scored} scored this run</span>
            </div>

            <ul className={styles.matchList}>
              {result.matches.map((m: Match, i: number) => (
                <li key={i} className={styles.matchCard}>
                  <div className={styles.matchHeader}>
                    <span
                      className={styles.categoryBadge}
                      style={{ backgroundColor: CATEGORY_COLORS[m.category] ?? "#6b7280" }}
                    >
                      {m.category} · {m.score}
                    </span>
                    <a className={styles.matchTitle} href={m.url} target="_blank" rel="noopener noreferrer">
                      {m.title}
                    </a>
                  </div>
                  <div className={styles.matchMeta}>
                    {m.company} · {m.location}
                  </div>
                  <p className={styles.matchReasoning}>{m.reasoning}</p>
                  {m.draft && (
                    <div className={styles.draftBox}>
                      <div className={styles.draftLabel}>Draft cover-letter opening (not sent — yours to edit)</div>
                      <p className={styles.draftText}>{m.draft}</p>
                    </div>
                  )}
                </li>
              ))}
            </ul>

            {result.matches.length === 0 && <p className={styles.noMatches}>No new postings this run.</p>}
          </>
        )}
      </main>
    </div>
  );
}
