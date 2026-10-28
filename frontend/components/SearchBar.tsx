"use client";

import { FormEvent, useState } from "react";

interface SearchBarProps {
  disabled: boolean;
  onSearch: (query: string) => void;
}

export default function SearchBar({ disabled, onSearch }: SearchBarProps) {
  const [query, setQuery] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed && !disabled) onSearch(trimmed);
  }

  return (
    <form className="flex flex-col gap-3 sm:flex-row" onSubmit={submit}>
      <label className="sr-only" htmlFor="search-query">
        Search products
      </label>
      <input
        id="search-query"
        className="min-w-0 flex-1 rounded-full border border-ink/15 bg-white px-6 py-4 text-base outline-none transition focus:border-moss focus:ring-2 focus:ring-moss/20"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Try “soft knit sweater”"
        maxLength={200}
        disabled={disabled}
      />
      <button className="button-primary" type="submit" disabled={disabled || !query.trim()}>
        Search
      </button>
    </form>
  );
}
