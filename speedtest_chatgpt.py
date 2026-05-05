import asyncio
import math
import statistics
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ProbeResult:
    rtt_ms: Optional[float]  # None means timeout/failure
    error: Optional[str] = None


def percentile(sorted_vals: List[float], p: float) -> float:
    """Linear interpolation percentile. p in [0, 100]."""
    if not sorted_vals:
        raise ValueError("No values for percentile.")
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


async def tcp_connect_rtt(host: str, port: int, timeout: float) -> ProbeResult:
    """
    Measures TCP connect "RTT-ish" latency: time to establish a TCP connection.
    Uses high-resolution monotonic clock (perf_counter_ns).
    """
    start_ns = time.perf_counter_ns()
    try:
        conn = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout)
        end_ns = time.perf_counter_ns()
        writer.close()
        # Ensure proper close on all platforms
        try:
            await writer.wait_closed()
        except Exception:
            pass
        rtt_ms = (end_ns - start_ns) / 1_000_000.0
        return ProbeResult(rtt_ms=rtt_ms)
    except Exception as e:
        return ProbeResult(rtt_ms=None, error=str(e))


def compute_jitter_metrics(rtts_ms: List[float]) -> dict:
    """
    Computes multiple jitter definitions from RTT samples.

    - rfc3550_jitter_ms: Smoothed jitter estimator (uses consecutive deltas)
    - mad_delta_ms: Mean absolute difference of consecutive RTTs
    - p95_minus_p50_ms: Tail-spike jitter indicator
    - stdev_ms: Standard deviation
    """
    if len(rtts_ms) < 2:
        return {
            "rfc3550_jitter_ms": None,
            "mad_delta_ms": None,
            "p95_minus_p50_ms": None,
            "stdev_ms": None,
        }

    # Consecutive absolute deltas
    deltas = [abs(rtts_ms[i] - rtts_ms[i - 1]) for i in range(1, len(rtts_ms))]

    # RFC3550-style smoothed jitter (adapted to RTT deltas)
    # J = J + (|D| - J) / 16
    J = 0.0
    for d in deltas:
        J += (d - J) / 16.0

    sorted_rtts = sorted(rtts_ms)
    p50 = percentile(sorted_rtts, 50)
    p95 = percentile(sorted_rtts, 95)

    return {
        "rfc3550_jitter_ms": J,
        "mad_delta_ms": statistics.mean(deltas),
        "p95_minus_p50_ms": p95 - p50,
        "stdev_ms": statistics.pstdev(rtts_ms),
    }


def compute_latency_stats(rtts_ms: List[float]) -> dict:
    if not rtts_ms:
        return {}
    s = sorted(rtts_ms)
    return {
        "count": len(rtts_ms),
        "min_ms": s[0],
        "mean_ms": statistics.mean(rtts_ms),
        "median_p50_ms": percentile(s, 50),
        "p95_ms": percentile(s, 95),
        "p99_ms": percentile(s, 99),
        "max_ms": s[-1],
    }


async def run_probe(
    host: str,
    port: int = 443,
    samples: int = 50,
    timeout: float = 1.5,
    interval: float = 0.10,
    warmup: int = 3,
) -> None:
    """
    Runs multiple TCP-connect probes.
    interval: sleep between probes (seconds).
    warmup: initial probes discarded to reduce cold-start effects.
    """
    results: List[ProbeResult] = []

    # Warmup (discarded)
    for _ in range(warmup):
        _ = await tcp_connect_rtt(host, port, timeout)
        await asyncio.sleep(interval)

    # Main sampling
    for _ in range(samples):
        res = await tcp_connect_rtt(host, port, timeout)
        results.append(res)
        await asyncio.sleep(interval)

    ok = [r.rtt_ms for r in results if r.rtt_ms is not None]
    ok = [x for x in ok if x is not None]
    failures = [r for r in results if r.rtt_ms is None]

    loss_pct = (len(failures) / len(results)) * 100.0 if results else 0.0

    print(f"\nTarget: {host}:{port}")
    print(f"Samples: {len(results)} (warmup discarded: {warmup})")
    print(f"Timeouts/Failures: {len(failures)} ({loss_pct:.1f}%)")

    if not ok:
        print("No successful RTT samples. Try increasing timeout or changing host/port.")
        if failures:
            print("Last error:", failures[-1].error)
        return

    lat = compute_latency_stats(ok)
    jit = compute_jitter_metrics(ok)

    print("\nLatency (ms):")
    print(
        f"  min {lat['min_ms']:.2f} | mean {lat['mean_ms']:.2f} | "
        f"p50 {lat['median_p50_ms']:.2f} | p95 {lat['p95_ms']:.2f} | "
        f"p99 {lat['p99_ms']:.2f} | max {lat['max_ms']:.2f}"
    )

    print("\nJitter (ms):")
    if jit["rfc3550_jitter_ms"] is not None:
        print(f"  RFC3550 smoothed jitter: {jit['rfc3550_jitter_ms']:.2f}")
        print(f"  Mean abs delta (consecutive): {jit['mad_delta_ms']:.2f}")
        print(f"  p95 - p50 (spike indicator): {jit['p95_minus_p50_ms']:.2f}")
        print(f"  Std dev: {jit['stdev_ms']:.2f}")
    else:
        print("  Not enough samples to compute jitter.")


if __name__ == "__main__":
    # Examples:
    # asyncio.run(run_probe("1.1.1.1", 443))
    # asyncio.run(run_probe("google.com", 443))
    asyncio.run(run_probe("1.1.1.1", port=443, samples=60, timeout=1.5, interval=0.10, warmup=3))
