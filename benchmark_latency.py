"""Measure p50/p95 latency of a RUNNING server: python benchmark_latency.py"""
import statistics, time, requests

BASE = "http://127.0.0.1:8000"
QUERIES = ["black hoodie", "red dress", "leather boots", "white sneakers", "denim jacket"] * 10


def run(label, queries):
    times = []
    for q in queries:
        t = time.perf_counter()
        requests.post(f"{BASE}/search/text", json={"query": q, "top_k": 10}).raise_for_status()
        times.append((time.perf_counter() - t) * 1000)
    times.sort()
    print(f"{label}: p50={statistics.median(times):.1f} ms  p95={times[int(len(times)*0.95)-1]:.1f} ms")


if __name__ == "__main__":
    # first pass: mostly cache MISS for each distinct query, then pass 2: cache HIT
    run("uncached (first pass, unique queries)", sorted(set(QUERIES)) )
    run("cached   (repeat queries)", QUERIES)
