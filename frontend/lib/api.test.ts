import { describe, expect, it } from "vitest";
import { parseRetryAfter } from "@/lib/useCountdown";

describe("parseRetryAfter", () => {
  it("parses delta-seconds", () => {
    expect(parseRetryAfter("12")).toBe(12);
  });

  it("parses an HTTP-date relative to now", () => {
    const now = Date.parse("Wed, 21 Oct 2015 07:27:00 GMT");
    expect(parseRetryAfter("Wed, 21 Oct 2015 07:27:08 GMT", now)).toBe(8);
  });

  it("returns zero for expired or invalid values", () => {
    expect(parseRetryAfter("Wed, 21 Oct 2015 07:27:00 GMT", Date.parse("Wed, 21 Oct 2015 07:27:08 GMT"))).toBe(0);
    expect(parseRetryAfter("not a date")).toBe(0);
    expect(parseRetryAfter(null)).toBe(0);
  });
});
