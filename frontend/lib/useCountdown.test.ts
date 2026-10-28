import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useCountdown } from "@/lib/useCountdown";

describe("useCountdown", () => {
  afterEach(() => vi.useRealTimers());

  it("counts down delta-seconds and expires", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2025-01-01T00:00:00Z"));
    const { result, rerender } = renderHook(
      ({ value }: { value: string | null }) => useCountdown(value),
      { initialProps: { value: null as string | null } },
    );

    rerender({ value: "2" });
    expect(result.current).toBe(2);
    act(() => {
      vi.advanceTimersByTime(1100);
    });
    expect(result.current).toBe(1);
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current).toBe(0);
  });

  it("counts down an HTTP-date Retry-After value", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2025-01-01T00:00:00Z"));
    const { result } = renderHook(() =>
      useCountdown("Wed, 01 Jan 2025 00:00:03 GMT"),
    );

    expect(result.current).toBe(3);
    act(() => {
      vi.advanceTimersByTime(1500);
    });
    expect(result.current).toBe(2);
  });
});
