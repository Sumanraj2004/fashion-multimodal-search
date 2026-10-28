"use client";

import Link from "next/link";
import { useState } from "react";
import type { Product } from "@/lib/types";

export default function ProductCard({ product }: { product: Product }) {
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <Link
      href={`/products/${encodeURIComponent(product.id)}`}
      className="group overflow-hidden rounded-2xl border border-ink/10 bg-white transition hover:-translate-y-1 hover:shadow-lg"
    >
      <div className="aspect-[4/5] overflow-hidden bg-cream">
        {product.image_url && !imageFailed ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.title}
            loading="lazy"
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="grid h-full place-items-center text-sm text-ink/45" role="img" aria-label="Image unavailable">
            Image unavailable
          </div>
        )}
      </div>
      <div className="p-4">
        <p className="truncate font-medium">{product.title}</p>
        {product.category && <p className="mt-1 text-sm text-ink/55">{product.category}</p>}
        {product.price !== null && product.price !== undefined && (
          <p className="mt-3 font-semibold">${product.price.toFixed(2)}</p>
        )}
      </div>
    </Link>
  );
}
