"use client";

import { useCallback, useState } from "react";
import CategoryFilter from "@/components/CategoryFilter";
import ErrorBanner from "@/components/ErrorBanner";
import ImageUpload from "@/components/ImageUpload";
import ResultsGrid from "@/components/ResultsGrid";
import SearchBar from "@/components/SearchBar";
import Skeleton from "@/components/Skeleton";
import StatusFooter from "@/components/StatusFooter";
import { ApiError, searchImage, searchText } from "@/lib/api";
import type { SearchResponse } from "@/lib/types";
import { useCountdown } from "@/lib/useCountdown";

type PreviousSearch =
  | { type: "text"; query: string }
  | { type: "image"; file: File };

export default function SearchPage() {
  const [category, setCategory] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);
  const [retryAfter, setRetryAfter] = useState<string | null>(null);
  const [previousSearch, setPreviousSearch] = useState<PreviousSearch | null>(null);
  const countdown = useCountdown(retryAfter);
  const disabled = loading || countdown > 0;

  const runSearch = useCallback(
    async (search: () => Promise<SearchResponse>, append = false) => {
      if (disabled) return;
      setLoading(true);
      setError(null);
      setRetryAfter(null);
      try {
        const result = await search();
        setResponse((previous) =>
          append && previous
            ? { ...result, results: [...previous.results, ...result.results] }
            : result,
        );
      } catch (caught) {
        const apiError =
          caught instanceof ApiError
            ? caught
            : new ApiError("An unexpected error occurred.", 0);
        setError(apiError);
        if (apiError.status === 429) setRetryAfter(apiError.retryAfter);
      } finally {
        setLoading(false);
      }
    },
    [disabled],
  );

  return (
    <main className="mx-auto max-w-7xl px-5 pb-12 pt-10 sm:pt-16">
      <header className="mb-16 flex items-center justify-between">
        <a href="/" className="text-lg font-bold tracking-tight">COMMON THREAD<span className="text-moss">.</span></a>
        <span className="text-xs uppercase tracking-[0.2em] text-ink/50">Research collection</span>
      </header>

      <section className="mx-auto mb-14 max-w-3xl text-center">
        <p className="mb-5 text-xs font-semibold uppercase tracking-[0.25em] text-moss">Find your next favorite</p>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">
          Search by feeling,
          <br className="hidden sm:block" /> not just by name.
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-ink/60">
          Explore a curated fashion collection with natural language or a visual reference.
        </p>
      </section>

      <section className="mx-auto max-w-4xl space-y-4 rounded-3xl border border-ink/10 bg-white/55 p-4 shadow-sm sm:p-6">
        <SearchBar
          disabled={disabled}
          onSearch={(query) => {
            setPreviousSearch({ type: "text", query });
            void runSearch(() => searchText({ query, category }))
          }}
        />
        <div className="flex flex-col justify-between gap-4 border-t border-ink/10 pt-4 sm:flex-row sm:items-center">
          <ImageUpload
            disabled={disabled}
            onSelect={(file) => {
              if (file) {
                setPreviousSearch({ type: "image", file });
                void runSearch(() => searchImage({ file, category }));
              }
            }}
          />
          <CategoryFilter value={category} onChange={setCategory} />
        </div>
      </section>

      <section className="mt-12 space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-moss">The edit</p>
            <h2 className="mt-1 text-2xl font-semibold">
              {response ? `${response.total_matches} matching pieces` : "A few things to get you started"}
            </h2>
          </div>
          {response && <p className="text-sm text-ink/50">Page {response.page}</p>}
        </div>

        {error && (
          <ErrorBanner message={error.message} status={error.status || null} countdown={countdown} />
        )}
        {loading ? (
          <Skeleton />
        ) : (
          <ResultsGrid products={response?.results ?? []} />
        )}
        {response?.has_more && response.page < 20 && previousSearch && (
          <button
            className="button-primary mx-auto block"
            disabled={disabled}
            onClick={() => {
              const page = response.page + 1;
              void runSearch(
                () =>
                  previousSearch.type === "text"
                    ? searchText({ query: previousSearch.query, page, category })
                    : searchImage({ file: previousSearch.file, page, category }),
                true,
              );
            }}
          >
            Load more
          </button>
        )}
        <StatusFooter tookMs={response?.took_ms ?? null} cached={response?.cached ?? null} />
      </section>
    </main>
  );
}
