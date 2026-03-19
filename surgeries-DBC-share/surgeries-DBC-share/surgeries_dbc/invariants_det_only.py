# surgeries_dbc/invariants_det_only.py
#
# Determinant-only invariants:
#   - compute det(K) = |Δ_K(-1)| for each knot,
# using SnapPy's dedicated determinant() method on links.
#
# This is meant for a lightweight pipeline where we only need detList.txt.

from __future__ import annotations

from typing import List

import snappy

from .models import KnotRecord


def _snappy_dt_string(dt_numeric: str) -> str:
    """
    Build the SnapPy DT string from a numeric DT code.

    Example:
        dt_numeric = "4,12,-16,-18,-22,-20,2,24,-6,-26,-10,14,-8"
        -> "DT: [(4,12,-16,-18,-22,-20,2,24,-6,-26,-10,14,-8)]"
    """
    return f"DT: [({dt_numeric.strip()})]"


def determinant_from_dt_numeric(dt_numeric: str) -> int:
    """
    Given a numeric DT code as a string, construct the SnapPy link and
    return its determinant as an integer.

    We rely on spherogram.Link.determinant(), which is exposed via
    SnapPy's Link class.
    """
    K = snappy.Link(_snappy_dt_string(dt_numeric))
    # Uses Goeritz / Wirtinger-style methods internally.
    return int(K.determinant())


def compute_determinants(records: List[KnotRecord]) -> None:
    """
    For each KnotRecord, compute det(K) from the DT code and store it in rec.det.

    This is designed to be used by run_det_pipeline.sage, which:
      - loads records via load_knot_records(base),
      - calls compute_determinants(records),
      - then writes detList.txt via write_det_list(base, records).
    """
    n = len(records)
    for i, rec in enumerate(records):
        # Allow re-runs: if det is already present, skip.
        if rec.det is not None:
            continue

        rec.det = determinant_from_dt_numeric(rec.dt_numeric)

        if n > 0 and i % 500 == 0:
            print(f"{i} / {n} determinants computed")
