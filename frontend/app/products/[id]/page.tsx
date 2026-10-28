"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import ErrorBanner from "@/components/ErrorBanner";
import ProductCard from "@/components/ProductCard";
import Skeleton from "@/components/Skeleton";
import StatusFooter from "@/components/StatusFooter";
import { ApiError, getProduct, searchText } from "@/lib/api";
import type { Product, SearchResponse } from "@/lib/types";
import { useCountdown } from "@/lib/useCountdown";

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [similar, setSimilar] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [retryAfter, setRetryAfter] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const countdown = useCountdown(retryAfter);

  const fetchProduct = useCallback(async () => {
    try {
      const current = await getProduct(params.id);
      setProduct(current);
      // There is no similar-items endpoint; use the current product title as a text-search query.
      const related = await searchText({ query: current.title, top_k: 13 });
      setSimilar({
        ...related,
        results: related.results.filter((item) => item.id !== current.id).slice(0, 12),
      });
      setError(null);
      setRetryAfter(null);
    } catch (caught) {
      const apiError =
        caught instanceof ApiError ? caught : new ApiError("An unexpected error occurred.", 0);
      setError(apiError);
      if (apiError.status === 429) setRetryAfter(apiError.retryAfter);
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void fetchProduct();
  }, [fetchProduct]);

  if (loading) {
    return <main className="mx-auto max-w-7xl px-5 py-16"><Skeleton count={4} /></main>;
  }

  return (
    <main className="mx-auto max-w-7xl px-5 pb-12 pt-10">
      <Link href="/" className="text-sm font-medium text-moss hover:underline">← Back to search</Link>
      {error && (
        <div className="mt-8">
          <ErrorBanner message={error.message} status={error.status || null} countdown={countdown} />
          {error.status === 429 && countdown === 0 && (
            <button className="button-primary mt-4" onClick={() => { setLoading(true); void fetchProduct(); }}>
              Retry
            </button>
          )}
        </div>
      )}
      {!product && !error && <p className="mt-8 text-ink/60">Product not found.</p>}
      {product && (
        <>
          <section className="mt-8 grid gap-10 md:grid-cols-2">
            <div className="overflow-hidden rounded-3xl bg-cream">
              {product.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={product.image_url} alt={product.title} className="max-h-[680px] w-full object-contain" />
              ) : (
                <div className="grid aspect-square place-items-center text-ink/45">Image unavailable</div>
              )}
            </div>
            <div className="flex flex-col justify-center">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-moss">{product.category ?? "Collection"}</p>
              <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-5xl">{product.title}</h1>
              {product.price !== null && product.price !== undefined && (
                <p className="mt-5 text-xl font-medium">${product.price.toFixed(2)}</p>
              )}
              <p className="mt-6 max-w-md leading-relaxed text-ink/60">
                Browse more pieces with a similar feel from across the collection.
              </p>
            </div>
          </section>
          <section className="mt-20 space-y-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-moss">Keep exploring</p>
              <h2 className="mt-1 text-2xl font-semibold">You might also like</h2>
              <p className="mt-2 text-sm text-ink/55">Selected by searching for this product&apos;s title.</p>
            </div>
            {similar ? (
              similar.results.length ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {similar.results.map((item) => <ProductCard key={item.id} product={item} />)}
                </div>
              ) : (
                <p className="text-sm text-ink/55">No similar products found.</p>
              )
            ) : (
              !error && <Skeleton count={4} />
            )}
            <StatusFooter tookMs={similar?.took_ms ?? null} cached={similar?.cached ?? null} />
          </section>
        </>
      )}
    </main>
  );
}
