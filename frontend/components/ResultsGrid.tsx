import type { Product } from "@/lib/types";
import ProductCard from "@/components/ProductCard";

export default function ResultsGrid({ products }: { products: Product[] }) {
  if (!products.length) {
    return (
      <div className="rounded-2xl border border-dashed border-ink/20 py-16 text-center text-ink/60">
        No products found. Try another search or category.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
