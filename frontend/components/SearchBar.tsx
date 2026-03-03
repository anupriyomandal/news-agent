"use client";

import { FormEvent, useState } from "react";

type Props = {
  onSearch: (query: string) => Promise<void>;
  loading: boolean;
};

export default function SearchBar({ onSearch, loading }: Props) {
  const [query, setQuery] = useState("");

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    await onSearch(query.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="mt-10 flex flex-col gap-3 sm:flex-row">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search geopolitical, market, or sector developments"
        className="w-full border border-rule bg-white px-4 py-3 text-base text-ink outline-none transition focus:border-ink"
      />
      <button
        type="submit"
        disabled={loading}
        className="border border-ink bg-ink px-5 py-3 text-sm font-medium uppercase tracking-wide text-paper transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-70"
      >
        {loading ? "Analyzing..." : "Search"}
      </button>
    </form>
  );
}
