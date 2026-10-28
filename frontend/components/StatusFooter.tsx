export default function StatusFooter({
  tookMs,
  cached,
}: {
  tookMs: number | null;
  cached: boolean | null;
}) {
  if (tookMs === null || cached === null) return null;

  return (
    <div className="flex items-center justify-between border-t border-ink/10 pt-4 text-xs text-ink/50">
      <span>Search completed in {tookMs.toFixed(1)} ms</span>
      <span>{cached ? "Served from cache" : "Fresh search"}</span>
    </div>
  );
}
