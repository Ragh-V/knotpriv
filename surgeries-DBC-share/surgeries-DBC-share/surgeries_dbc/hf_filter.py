# surgeries_dbc/hf_filter.py
#
# Stage 2: HF rank-only filter.
# Given KnotRecords with det, m, n, HFbound set, compute:
#   - which knots/slopes survive HF (hf_candidates),
#   - a simple log of what happened for each knot.

from __future__ import annotations

from typing import Dict, List, Tuple
import math

from .models import KnotRecord
from .hf_casson import DTconvertFull  # reuse existing DT conversion


def rank(m: int, n: int, p: int, q: int) -> int:
    """Rank-like lower bound function R(m,n,p,q) = |p - m q| + n|q|."""
    return abs(p - m * q) + n * abs(q)


def min_rank(m: int, n: int, p: int) -> int:
    """
    Minimal possible R(m,n,p,q) over a small, theoretically relevant set
    of q: {±1, floor(p/m), ceil(p/m)} when m ≠ 0, and {±1} when m = 0.
    """
    if m == 0:
        # Rank is |p| + n|q|, minimized at |q| = 1.
        return abs(p) + n

    q1 = 1
    q2 = -1
    sing = p / m

    if abs(sing) < 1:
        return min(rank(m, n, p, q1), rank(m, n, p, q2))
    else:
        q3 = math.floor(sing)
        q4 = math.ceil(sing)
        return min(
            rank(m, n, p, q1),
            rank(m, n, p, q2),
            rank(m, n, p, q3),
            rank(m, n, p, q4),
        )


def qminus(HFbound: int, p: int, m: int, n: int) -> int:
    """
    Lower bound q_- for the q-range where HF rank might be ≤ HFbound.
    Mirrors the original Sage code.
    """
    if m == 0:
        HFsing = 0
    else:
        HFsing = n * abs(p / m)

    if (m == -n and HFbound == HFsing):
        qtemp = math.ceil(p / m)
        return 1 if qtemp == 0 else qtemp
    elif (m < 0 and HFbound > HFsing):
        qtemp = math.ceil((HFbound + p) / (m - n))
        return 1 if qtemp == 0 else qtemp
    else:
        qtemp = math.ceil(-(HFbound - p) / (m + n))
        return 1 if qtemp == 0 else qtemp


def qplus(HFbound: int, p: int, m: int, n: int) -> int:
    """
    Upper bound q_+ for the q-range where HF rank might be ≤ HFbound.
    Mirrors the original Sage code.
    """
    if m == 0:
        HFsing = 0
    else:
        HFsing = n * abs(p / m)

    if (m == n and HFbound == HFsing):
        qtemp = math.floor(p / m)
        return -1 if qtemp == 0 else qtemp
    elif (m > 0 and HFbound > HFsing):
        qtemp = math.floor((HFbound + p) / (m + n))
        return -1 if qtemp == 0 else qtemp
    else:
        qtemp = math.floor(-(HFbound - p) / (m - n))
        return -1 if qtemp == 0 else qtemp


def hf_filter(records: List[KnotRecord]) -> Tuple[List[str], Dict[int, List[int]]]:
    """
    HF-only filter.

    Returns:
      - log: list of human-readable messages,
      - hf_candidates: dict mapping record index -> list of q's that survive HF.
    """
    log: List[str] = []
    hf_candidates: Dict[int, List[int]] = {}

    for idx, rec in enumerate(records):
        # NOTE: attribute is HFbound (as set by attach_hf_data), not hf_bound
        if rec.det is None or rec.m is None or rec.n is None or rec.HFbound is None:
            log.append(f"[HF] Skipping {rec.name}: missing det/m/n/HFbound.")
            continue

        p = abs(int(rec.det))
        m = int(rec.m)
        n = int(rec.n)
        HFbound = int(rec.HFbound)

        mini = min_rank(m, n, p)
        if mini > HFbound:
            log.append(
                f"[HF] Obstruction succeeds for {rec.name}: "
                f"minRank={mini} > HFbound={HFbound}."
            )
            continue

        # HF obstruction fails: generate candidate q's
        q_lo = qminus(HFbound, p, m, n)
        q_hi = qplus(HFbound, p, m, n)

        qs: List[int] = []
        for q in range(q_lo, q_hi + 1):
            if q == 0:
                continue
            if math.gcd(q, p) != 1:
                continue
            qs.append(q)

        if qs:
            hf_candidates[idx] = qs
            log.append(
                f"[HF] Obstruction fails for {rec.name}: "
                f"p={p}, q in {qs}."
            )
        else:
            log.append(
                f"[HF] Obstruction borderline for {rec.name} "
                f"(minRank={mini} ≤ HFbound={HFbound}) but no coprime slopes in range."
            )

    return log, hf_candidates


def write_hf_fail_list(base, records: List[KnotRecord], hf_candidates: Dict[int, List[int]]) -> None:
    """
    Write an initial HF-only 'fail list' to hf_failList.txt.

    Format per line:
      name; DT:[...]; p = <p>; q = [q1, q2, ...]
    where q's are the slopes that *pass* the HF filter and need Casson/TV.
    """
    lines: List[str] = []
    for idx, qs in hf_candidates.items():
        rec = records[idx]
        p = abs(int(rec.det))
        dt_full = DTconvertFull(rec.dt_alpha)
        line = f"{rec.name}; {dt_full}; p = {p}; q = {qs}"
        lines.append(line.replace("\n", " "))

    (base / "hf_failList.txt").write_text("\n".join(lines))
