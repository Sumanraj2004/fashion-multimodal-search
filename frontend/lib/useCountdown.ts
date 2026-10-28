"use client";

import { useEffect, useState } from "react";

export function parseRetryAfter(value: string | null, now = Date.now()): number {
  if (!value) return 0;

  const trimmed = value.trim();
  if (/^\d+$/.test(trimmed)) return Number(trimmed);

  const deadline = Date.parse(trimmed);
  if (Number.isNaN(deadline)) return 0;
  return Math.max(0, Math.ceil((deadline - now) / 1000));
}

export function useCountdown(retryAfter: string | null): number {
  const [secondsRemaining, setSecondsRemaining] = useState(0);

  useEffect(() => {
    const deadline = Date.now() + parseRetryAfter(retryAfter) * 1000;
    const update = () =>
      setSecondsRemaining(Math.max(0, Math.ceil((deadline - Date.now()) / 1000)));

    update();
    if (deadline <= Date.now()) return;

    const timer = window.setInterval(update, 250);
    return () => window.clearInterval(timer);
  }, [retryAfter]);

  return secondsRemaining;
}
