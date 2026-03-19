# surgeries_dbc/hf_casson.py
#
# Heegaard Floer rank obstruction + Casson comparison, acting on
# KnotRecord objects and using classical invariants stored there.

from pathlib import Path
from typing import List

from sage.all import Rational, gcd, ceil, floor  # Sage helpers
from sage.misc.parser import Parser

from .models import KnotRecord

# --------------------------------------------------------------------
# Helper: convert alphabetical DT code to "DT:[...]" string for logging
# --------------------------------------------------------------------

def DTconvertFull(dt_line: str) -> str:
    new_dt = "DT:["
    for x in dt_line:
        if x == "\n":
            continue
        elif ord(x) > 95:
            y = 2 * (ord(x) - 96)
            new_dt += f"{y},"
        else:
            y = -2 * (ord(x) - 64)
            new_dt += f"{y},"
    if new_dt.endswith(","):
        new_dt = new_dt[:-1]
    new_dt += "]"
    return new_dt

# --------------------------------------------------------------------
# Dedekind sum and rank helpers
# --------------------------------------------------------------------

def function1(t):
    """
    f(t) = 0 if t is an integer, = {t} - 1/2 otherwise.
    """
    from math import floor
    if floor(t) == t:
        return 0
    else:
        return t - floor(t) - 1/2

_dedekind_cache = {}

def dedekind(q, p):
    key = (int(q), int(p))
    if key in _dedekind_cache:
        return _dedekind_cache[key]
    total = 0
    for k in range(1, abs(int(p))):
        total += function1(k/p) * function1(k*q/p)
    _dedekind_cache[key] = total
    return total

def rank(m, n, p, q):
    return abs(p - m*q) + n*abs(q)

def minRank(m, n, p):
    if m == 0:
        return abs(p) + n
    sing = p / m
    q_candidates = [1, -1]
    if abs(sing) >= 1:
        q_candidates.extend([floor(sing), ceil(sing)])
    return min(rank(m, n, p, q) for q in q_candidates)

def qminus(HFbound, p, m, n):
    if m == 0:
        HFsing = 0
    else:
        HFsing = n*abs(p/m)
    if (m == -n and HFbound == HFsing):
        qtemp = ceil(p/m)
        return 1 if qtemp == 0 else qtemp
    elif (m < 0 and HFbound > HFsing):
        qtemp = ceil((HFbound + p)/(m-n))
        return 1 if qtemp == 0 else qtemp
    else:
        qtemp = ceil(-(HFbound - p)/(m+n))
        return 1 if qtemp == 0 else qtemp

def qplus(HFbound, p, m, n):
    if m == 0:
        HFsing = 0
    else:
        HFsing = n*abs(p/m)
    if (m == n and HFbound == HFsing):
        qtemp = floor(p/m)
        return -1 if qtemp == 0 else qtemp
    elif (m > 0 and HFbound > HFsing):
        qtemp = floor((HFbound + p)/(m+n))
        return -1 if qtemp == 0 else qtemp
    else:
        qtemp = floor(-(HFbound - p)/(m-n))
        return -1 if qtemp == 0 else qtemp

# --------------------------------------------------------------------
# Attach HF data from text files (mList, nList, HFboundList)
# --------------------------------------------------------------------

def attach_hf_data(base: Path, records: List[KnotRecord]) -> None:
    """
    Read mList.txt, nList.txt, HFboundList.txt and attach m, n, HFbound
    to each KnotRecord.
    """
    par = Parser()
    m_lines  = (base / "mList.txt").read_text().splitlines()
    n_lines  = (base / "nList.txt").read_text().splitlines()
    hf_lines = (base / "HFboundList.txt").read_text().splitlines()

    if not (len(records) == len(m_lines) == len(n_lines) == len(hf_lines)):
        raise ValueError("Lengths of mList, nList, HFboundList do not match knot list.")

    for rec, m_s, n_s, hf_s in zip(records, m_lines, n_lines, hf_lines):
        rec.m = par.parse(m_s.strip())
        rec.n = par.parse(n_s.strip())
        rec.HFbound = par.parse(hf_s.strip())

# --------------------------------------------------------------------
# Main HF + Casson comparison
# --------------------------------------------------------------------

import time

def run_hf_casson(records: List[KnotRecord]):
    """
    Perform the HF rank obstruction and Casson comparison.
    Returns: 
        yaml_data: list of dicts formatted for YAML dump
        profile_lines: list of strings containing micro-profiling data
        fail_list: list of strings (knot names) that failed Casson and need TV check
    """
    yaml_data = []
    profile_lines = []
    fail_list = []
    
    num_knots = len(records)

    for k, rec in enumerate(records):
        if k % 1000 == 0:
            print(f"HF/Casson Progress: {k}/{num_knots}")

        knot_start = time.perf_counter()
        
        # Base dictionary for this knot
        knot_entry = {
            "DT_code": rec.name,
            "pass_fail_HF_check": "",
            "CASSON_COMPARISON_RESULTS": []
        }

        p = abs(int(rec.det))
        m = rec.m
        n = rec.n
        HFbound = rec.HFbound

        cassonDBC = Rational(str(rec.casson_dbc))
        aval      = Rational(str(rec.A))

        # --- HF Profiling & Logic ---
        t_hf_start = time.perf_counter()
        mini = minRank(m, n, p)
        rec.hf_min_rank = mini
        rec.hf_obstruction_success = mini > HFbound
        hf_elapsed = time.perf_counter() - t_hf_start

        # --- Casson Profiling & Logic ---
        t_casson_start = time.perf_counter()
        if mini <= HFbound:
            # HF obstruction fails, attempt Casson
            knot_entry["pass_fail_HF_check"] = "HF obstruction fails"
            rec.casson_fail_q = []
            computed_cassons = []
            
            q_lo = qminus(HFbound, p, m, n)
            q_hi = qplus(HFbound, p, m, n)

            for q in [qq for qq in range(q_lo, q_hi+1) if (qq != 0 and gcd(qq, p) == 1)]:
                cassonSurgery = Rational(q*aval / p - dedekind(q, p)/2)
                computed_cassons.append(f"q={q}: {cassonSurgery}")
                
                if abs(cassonSurgery) == abs(cassonDBC):
                    rec.casson_fail_q.append(int(q))

            if not rec.casson_fail_q:
                knot_entry["CASSON_COMPARISON_RESULTS"] = [
                    "Successfully distinguished by Casson invariants.",
                    f"Computed variants: {', '.join(computed_cassons)}"
                ]
            else:
                knot_entry["CASSON_COMPARISON_RESULTS"] = [
                    "Casson invariants failed to distinguish.",
                    f"Failing q values: {rec.casson_fail_q}"
                ]
                # Both HF and Casson failed; queue this knot for Turaev-Viro
                fail_list.append(rec.name)
        else:
            # HF obstruction succeeds
            knot_entry["pass_fail_HF_check"] = "HF obstruction success!"
            knot_entry["CASSON_COMPARISON_RESULTS"] = ["Skipped (HF Success)"]
            
        casson_elapsed = time.perf_counter() - t_casson_start
        knot_total_elapsed = time.perf_counter() - knot_start
        
        # Append data to return lists
        yaml_data.append(knot_entry)
        profile_lines.append(f"{rec.name} | {hf_elapsed:.6f} | {casson_elapsed:.6f} | {knot_total_elapsed:.6f}")

    return yaml_data, profile_lines, fail_list
