export default function Skeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4" aria-label="Loading products" aria-busy="true">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="animate-pulse overflow-hidden rounded-2xl border border-ink/10 bg-white">
          <div className="aspect-[4/5] bg-ink/10" />
          <div className="space-y-2 p-4">
            <div className="h-4 w-4/5 rounded bg-ink/10" />
            <div className="h-3 w-2/5 rounded bg-ink/10" />
          </div>
        </div>
      ))}
    </div>
  );
}
