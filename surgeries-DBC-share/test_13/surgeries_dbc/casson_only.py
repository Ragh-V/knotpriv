# surgeries_dbc/casson_only.py
#
# Casson-only stage:
#   Given:
#     - records: list of KnotRecord with det, A, casson_dbc already set
#     - hf_candidates: dict[index -> list of slopes q surviving HF stage]
#   We:
#     - compute Casson invariants of p/q-surgeries using the standard formula
#       lambda(S^3_{p/q}(K)) = q/p * A(K) - s(q,p)/2,
#       where s(q,p) is the Dedekind sum,
#     - log, for each tested (K, q),
#         * Casson(DBC)
#         * Casson(p/q surgery)
#         * whether Casson distinguishes or fails,
#     - and populate rec.casson_fail_q with the slopes where Casson fails
#       (i.e. |lambda(surgery)| == |lambda(DBC)|).
#
# The detailed log is returned as a list of strings, which run_fast_pipeline
# appends to the HF log and writes to Casson-comparison-results.txt via
# write_hf_outputs.

from __future__ import annotations

from typing import Dict, List

import sympy as sym

from .models import KnotRecord

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
    # sym.floor works fine on rationals
    if x == sym.floor(x):
        return sym.Rational(0)
    return x - sym.floor(x) - sym.Rational(1, 2)


def dedekind_sum(q: int, p: int) -> sym.Rational:
    """
    Exact Dedekind sum:
        s(q,p) = sum_{k=1}^{|p|-1} ((k/p)) * ((kq/p))
    Returns a sym.Rational.

    We assume p != 0 and typically work with p = |det(K)|.
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
) -> List[str]:
    """
    For each knot index i in hf_candidates and each slope q in hf_candidates[i],
    compute the Casson invariant of the p/q-surgery and compare it with the
    Casson invariant of the double branched cover stored in rec.casson_dbc.

    - rec.det is used to define p = |det(K)|.
    - rec.A   is the A(K) value from the Alexander polynomial.
    - rec.casson_dbc is the Casson invariant of the DBC.

    We:
      * record, for each (K, q), a detailed line:
          "K = ..., p = ..., q = ... :
             Casson( DBC )    = ...
             Casson( surgery ) = ...
             -> [distinguishes / fails to distinguish]"
      * append q to rec.casson_fail_q when |Casson(surgery)| == |Casson(DBC)|.

    Returns:
      A list of log lines (strings) to be appended to the HF log and written
      to Casson-comparison-results.txt.
    """
    log: List[str] = []

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

        # Ensure we have a place to store failing slopes
        if rec.casson_fail_q is None:
            rec.casson_fail_q = []

        for q in hf_candidates[idx]:
            qR = sym.Rational(q)

            # Casson invariant of p/q-surgery:
            #   lambda(S^3_{p/q}(K)) = (q/p)*A(K) - s(q,p)/2
            s_qp = dedekind_sum(q, p)
            casson_surgery = qR * A / p - s_qp / 2
            casson_surgery = sym.simplify(casson_surgery)

            # Compare absolute values (as in the original script)
            distinguishes = (sym.Abs(casson_surgery) != sym.Abs(casson_dbc))

            # Verbose reporting:
            log.append(
                f"K = {rec.name}, p = {p}, q = {q}:"
            )
            log.append(
                f"  Casson( DBC )     = {casson_dbc}"
            )
            log.append(
                f"  Casson( surgery ) = {casson_surgery}"
            )

            if distinguishes:
                log.append("  -> Casson distinguishes DBC from surgery.")
            else:
                log.append("  -> Casson FAILS to distinguish (abs values agree).")
                rec.casson_fail_q.append(q)

    return log
