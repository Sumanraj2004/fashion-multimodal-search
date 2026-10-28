export default function ErrorBanner({
  message,
  status,
  countdown,
}: {
  message: string;
  status: number | null;
  countdown: number;
}) {
  return (
    <div
      className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-900"
      role="alert"
    >
      <p className="font-semibold">{status === 429 ? "Search limit reached" : "Could not complete the request"}</p>
      <p className="mt-1">{message}</p>
      {status === 429 && countdown > 0 && (
        <p className="mt-2 font-medium">
          You can search again in {countdown} second{countdown === 1 ? "" : "s"}.
        </p>
      )}
    </div>
  );
}
