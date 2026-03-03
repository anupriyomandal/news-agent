"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import ArticleSection from "@/components/ArticleSection";
import Divider from "@/components/Divider";
import MetadataLine from "@/components/MetadataLine";
import SearchBar from "@/components/SearchBar";
import TLDRBox from "@/components/TLDRBox";
import { searchNews } from "@/styles/api";
import type { Report } from "@/styles/types";

export default function HomePage() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [statusIndex, setStatusIndex] = useState(0);

  const loadingMessages = [
    "Searching Reuters, BBC, The Hindu, and TechCrunch coverage.",
    "Retrieving semantically relevant articles from the vector index.",
    "Extracting factual developments from selected reports.",
    "Merging overlapping facts and organizing structured sections.",
    "Synthesizing TL;DR and full analytical brief.",
  ];

  useEffect(() => {
    if (!loading) {
      setProgress(0);
      setStatusIndex(0);
      return;
    }

    const progressTimer = window.setInterval(() => {
      setProgress((current) => {
        if (current >= 92) return current;
        return Math.min(92, current + Math.max(1.2, (92 - current) * 0.09));
      });
    }, 350);

    const messageTimer = window.setInterval(() => {
      setStatusIndex((current) => (current + 1) % loadingMessages.length);
    }, 2200);

    return () => {
      window.clearInterval(progressTimer);
      window.clearInterval(messageTimer);
    };
  }, [loading]);

  const runSearch = async (query: string) => {
    setLoading(true);
    setProgress(7);
    setError(null);
    try {
      const result = await searchNews(query);
      setReport(result);
      setProgress(100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run analysis");
      setReport(null);
    } finally {
      window.setTimeout(() => setLoading(false), 250);
    }
  };

  return (
    <main className="mx-auto max-w-article px-6 pb-20 pt-14">
      <header>
        <p className="font-ui text-xs uppercase tracking-[0.2em] text-muted">Anupriyo Mandal&apos;s News Intelligence Engine</p>
        <h1 className="mt-4 font-headline text-5xl leading-tight text-ink">The Signal</h1>
        <p className="mt-3 max-w-[640px] font-body text-lg leading-8 text-muted">
          Enter a topic to synthesize recent RSS coverage into a structured analytical report.
        </p>
      </header>

      <SearchBar onSearch={runSearch} loading={loading} />

      {loading ? (
        <section className="mt-4 border border-rule bg-white px-4 py-3">
          <p className="font-ui text-[0.78rem] uppercase tracking-[0.14em] text-muted">Analysis Progress</p>
          <div className="mt-2 h-2 w-full overflow-hidden bg-[#e4e3de]">
            <div
              className="h-full bg-ink transition-[width] duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="mt-2 font-body text-[0.98rem] leading-7 text-muted">{loadingMessages[statusIndex]}</p>
        </section>
      ) : null}

      {error ? <p className="mt-4 font-ui text-sm text-red-700">{error}</p> : null}

      {report ? (
        <article className="mt-14">
          <h2 className="font-headline text-[3rem] leading-[1.12] text-ink">{report.headline}</h2>
          <div className="mt-4 flex items-center justify-between gap-3">
            <MetadataLine text={report.metadata} />
            <Link
              href={`/article/${report.report_id}`}
              className="font-ui text-xs uppercase tracking-[0.14em] text-muted underline decoration-rule underline-offset-4"
            >
              Open Full View
            </Link>
          </div>

          <Divider />
          <TLDRBox points={report.tldr} />

          {Object.entries(report.sections).map(([title, content]) => (
            <ArticleSection key={title} title={title} content={content} />
          ))}

          <section className="mb-10">
            <h3 className="font-headline text-[1.8rem] leading-tight">Implications / What Analysts Are Watching</h3>
            <p className="mt-3 font-body text-[1.07rem] leading-8">{report.implications}</p>
          </section>

          <Divider />
          <section>
            <h3 className="font-headline text-[1.8rem]">Sources Referenced</h3>
            <ul className="mt-4 space-y-2 font-body text-[1.02rem] leading-7">
              {report.sources.map((source) => (
                <li key={source.url}>
                  <a href={source.url} target="_blank" rel="noreferrer" className="underline underline-offset-4">
                    {source.title}
                  </a>{" "}
                  <span className="text-muted">({source.source})</span>
                </li>
              ))}
            </ul>
          </section>
        </article>
      ) : null}
    </main>
  );
}
