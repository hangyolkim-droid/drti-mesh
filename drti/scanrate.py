"""Scan-rate bound.

On unrooted commodity phones the OS sandbox blocks monitor-mode capture, so
links are probed as sequential pairwise unicast on a half-duplex channel. Full
mesh scan time therefore grows with the link count L = N(N-1)/2:

    scan_hz = 1 / (L * link_time)

`link_time` (per-link measurement time) is an *assumption*, not a measurement.
The default 10 ms reproduces the baseline table (4/6/8/10 nodes -> ~16/7/3.5/2.2 Hz).
"""

from .geometry import link_count

DEFAULT_LINK_TIME_S = 0.010


def scan_hz(n, link_time=DEFAULT_LINK_TIME_S):
    """Full-mesh scan rate in Hz."""
    return 1.0 / (link_count(n) * link_time)


def sample_spacing(speed_mps, hz):
    """Distance walked between scans, in metres."""
    return speed_mps / hz


def table(node_counts=(4, 6, 8, 10, 12), link_time=DEFAULT_LINK_TIME_S):
    return [(n, link_count(n), scan_hz(n, link_time)) for n in node_counts]
