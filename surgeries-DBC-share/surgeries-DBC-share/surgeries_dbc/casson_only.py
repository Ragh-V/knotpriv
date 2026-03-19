# surgeries_dbc/casson_only.py
from __future__ import annotations
from typing import Dict, List, Tuple, Any
import sympy as sym
from models import KnotRecord

# --------------------------------------------------------------------
# Exact sawtooth and Dedekind sum
# --------------------------------------------------------------------

def _sawtooth(x: sym.Rational) -> sym.Rational:
    """
    Sawtooth function:
        ((x)) = 0                if x is an integer
               x - floor(x) - 1/2 otherwise
    Implemented with exact rationals.
    """
    if x == sym.floor(x):
        return sym.Rational(0)
    return x - sym.floor(x) - sym.Rational(1, 2)

def dedekind_sum(q: int, p: int) -> sym.Rational:
    """
    Exact Dedekind sum:
        s(q,p) = sum_{k=1}^{|p|-1} ((k/p)) * ((kq/p))
    """
    P = abs(int(p))
    if P == 0:
        raise ValueError("Dedekind sum called with p = 0")

    total = sym.Rational(0)
    for k in range(1, P):
        x1 = sym.Rational(k, P)
        x2 = sym.Rational(k * q, P)
        total += _sawtooth(x1) * _sawtooth(x2)
    return sym.simplify(total)

# --------------------------------------------------------------------
# Main Casson-only driver
# --------------------------------------------------------------------

def run_casson_on_candidates(
    records: List[KnotRecord],
    hf_candidates: Dict[int, List[int]],
) -> Tuple[List[str], Dict[int, List[Dict[str, Any]]]]:
    """
    Returns:
      1. List of log strings (for text file output).
      2. Dictionary mapping knot_index -> List of result dictionaries (for YAML/JSON).
    """
    print(f"Running Casson comparisons on {len(hf_candidates)} knots...")
    log: List[str] = []
    
    # Structure: { knot_index: [ {q: 2, dbc: '1/2', surgery: '1/2', distinguishes: False}, ... ] }
    structured_data: Dict[int, List[Dict[str, Any]]] = {}

    for idx in sorted(hf_candidates.keys()):
        rec = records[idx]

        # Basic data for this knot
        if rec.det is None:
            raise ValueError(f"Determinant missing for record {rec.name}")
        if rec.A is None:
            raise ValueError(f"A(K) missing for record {rec.name}")
        if rec.casson_dbc is None:
            raise ValueError(f"Casson( DBC ) missing for record {rec.name}")

        p = abs(int(rec.det))
        A = sym.Rational(rec.A)
        casson_dbc = sym.Rational(rec.casson_dbc)

        log.append("")
        log.append(f"--- Casson comparison for {rec.name} (p = {p}) ---")

        if rec.casson_fail_q is None:
            rec.casson_fail_q = []

        knot_results = []

        for q in hf_candidates[idx]:
            qR = sym.Rational(q)

            # Casson invariant of p/q-surgery
            s_qp = dedekind_sum(q, p)
            casson_surgery = qR * A / p - s_qp / 2
            casson_surgery = sym.simplify(casson_surgery)

            # Compare absolute values
            distinguishes = (sym.Abs(casson_surgery) != sym.Abs(casson_dbc))

            # --- Text Logging ---
            log.append(f"K = {rec.name}, p = {p}, q = {q}:")
            log.append(f"  Casson( DBC )     = {casson_dbc}")
            log.append(f"  Casson( surgery ) = {casson_surgery}")

            if distinguishes:
                log.append("  -> Casson distinguishes DBC from surgery.")
            else:
                log.append("  -> Casson FAILS to distinguish (abs values agree).")
                rec.casson_fail_q.append(q)

            # --- Structured Data for YAML ---
            knot_results.append({
                "q": int(q),
                "p": int(p),
                "casson_dbc": str(casson_dbc),         # Convert to string to avoid serialization errors
                "casson_surgery": str(casson_surgery), # Convert to string
                "distinguishes": bool(distinguishes)
            })

        structured_data[idx] = knot_results

    return log, structured_data

if __name__ == "__main__":
    # Dummy run for testing
    run_casson_on_candidates([], {})