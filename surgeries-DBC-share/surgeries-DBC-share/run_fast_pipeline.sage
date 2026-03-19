# run_fast_pipeline.sage
#
# Fast pipeline:
#   0. If failList.txt exists, skip straight to TV-compare (Stage 8).
#   1. Ensure numDTList.txt exists (DT-convert.sage).
#   2. Load knot records.
#   3. Determinants:
#        - if detList.txt exists, load det(K) from file;
#        - otherwise compute det(K) and write detList.txt.
#   4. Attach HF data (m, n, HFbound).
#   5. HF-only filter -> hf_candidates, hf_failList.txt.
#   6. Classical invariants *only for HF-survivor knots*, with per-index caching
#      via aList/sigList/jonesList/cassonList.
#   7. Casson-only test on HF-survivors -> failList.txt (final).
#   8. TV-compare on survivors (via failList.txt).

import sys
from pathlib import Path

import sympy as sym

sys.path.append("/repo")

from surgeries_dbc.io import (
    load_knot_records,
    write_hf_outputs,
)
from surgeries_dbc.invariants_det_only import compute_determinants
from surgeries_dbc.invariants import compute_classical_invariants
from surgeries_dbc.hf_casson import attach_hf_data
from surgeries_dbc.hf_filter import hf_filter, write_hf_fail_list
from surgeries_dbc.casson_only import run_casson_on_candidates
from surgeries_dbc.tv_compare import run_tv_compare

BASE = Path("/work").resolve()

print("=== Fast pipeline ===")

# ---------------------------------------------------------------------
# Early exit: if failList.txt already exists, skip straight to TV stage
# ---------------------------------------------------------------------
fail_path = BASE / "failList.txt"
if fail_path.exists():
    print("[TV-only] failList.txt found; skipping determinant/HF/Casson stages.")
    print("=== Step 8: Turaev–Viro comparison ===")
    tv_ok = run_tv_compare(BASE)
    if tv_ok:
        print("=== Fast pipeline complete (TV-only rerun) ===")
    else:
        print("=== Pipeline halted early in TV stage (slow cover); re-run to continue. ===")
    sys.exit(0)

# ---------------------------------------------------------------------
# Step 1: Ensure numDTList.txt exists (for numeric DT -> SnapPy)
# ---------------------------------------------------------------------
num_dt_path = BASE / "numDTList.txt"
if num_dt_path.exists():
    print("[Step 1] numDTList.txt found.")
else:
    print("[Step 1] numDTList.txt missing; running DT-convert.sage...")
    load("/repo/DT-convert.sage")

# ---------------------------------------------------------------------
# Step 2: Load knot records (names, DTList, numDTList)
# ---------------------------------------------------------------------
print("[Step 2] Loading knot records...")
records = load_knot_records(BASE)
n_knots = len(records)
print(f"[Step 2] Loaded {n_knots} knots.")

# ---------------------------------------------------------------------
# Step 3: Determinants with caching via detList.txt
# ---------------------------------------------------------------------
det_path = BASE / "detList.txt"

if det_path.exists():
    print("[Step 3] detList.txt found; loading determinants from file.")
    det_lines = det_path.read_text().splitlines()
    if len(det_lines) != n_knots:
        raise ValueError(
            f"detList.txt length {len(det_lines)} does not match "
            f"number of records {n_knots}."
        )
    for rec, d_s in zip(records, det_lines):
        rec.det = int(d_s.strip())
else:
    print("[Step 3] detList.txt not found; computing determinants via SnapPy...")
    compute_determinants(records)
    det_lines = [str(rec.det) for rec in records]
    det_path.write_text("\n".join(det_lines))
    print(f"[Step 3] detList.txt written to {det_path}")

# ---------------------------------------------------------------------
# Step 4: Attach HF data (m, n, HFbound)
# ---------------------------------------------------------------------
print("[Step 4] Attaching HF data (m, n, HFbound) from mList/nList/HFboundList...")
# Important: attach_hf_data mutates 'records' in-place and returns None.
# Do *not* assign its return value back to 'records'.
attach_hf_data(BASE, records)

# ---------------------------------------------------------------------
# Step 5: HF-only filter -> hf_candidates, hf_failList.txt
# ---------------------------------------------------------------------
print("[Step 5] Running HF-only filter...")
hf_log, hf_candidates = hf_filter(records)
write_hf_fail_list(BASE, records, hf_candidates)

if not hf_candidates:
    print("[Step 5] HF obstruction ruled out all slopes; no need for Casson or TV.")
    # Write empty failList.txt so TV stage sees no work.
    fail_path.write_text("")
    sys.exit(0)

print(f"[Step 5] HF-surviving knots: {len(hf_candidates)}")

# ---------------------------------------------------------------------
# Step 6: Classical invariants ONLY for HF-survivors, with per-index caching
# ---------------------------------------------------------------------
a_path      = BASE / "aList.txt"
sig_path    = BASE / "sigList.txt"
jones_path  = BASE / "jonesList.txt"
casson_path = BASE / "cassonList.txt"

def _read_or_blank(path: Path, n: int):
    """
    Return a list of length n:
      - if 'path' exists: its lines (must have length n),
      - otherwise: a list of n empty strings.
    """
    if path.exists():
        lines = path.read_text().splitlines()
        if len(lines) != n:
            raise ValueError(
                f"{path.name} length {len(lines)} does not match "
                f"number of records {n}."
            )
        return lines
    else:
        return [""] * n

# Load existing lines (or blanks) for all knots
a_lines      = _read_or_blank(a_path, n_knots)
sig_lines    = _read_or_blank(sig_path, n_knots)
jones_lines  = _read_or_blank(jones_path, n_knots)
casson_lines = _read_or_blank(casson_path, n_knots)

candidate_indices = sorted(hf_candidates.keys())

need_compute = []
for idx in candidate_indices:
    have_all = (
        a_lines[idx].strip() != "" and
        sig_lines[idx].strip() != "" and
        jones_lines[idx].strip() != "" and
        casson_lines[idx].strip() != ""
    )
    if have_all:
        # Load invariants into the record from stored strings
        records[idx].A           = sym.sympify(a_lines[idx].strip())
        records[idx].signature   = int(sig_lines[idx].strip())
        records[idx].jones_expr  = sym.sympify(jones_lines[idx].strip())
        records[idx].casson_dbc  = sym.sympify(casson_lines[idx].strip())
    else:
        need_compute.append(idx)

if need_compute:
    print(f"[Step 6] Computing classical invariants for {len(need_compute)} HF-survivor knots...")
    subset = [records[i] for i in need_compute]
    compute_classical_invariants(subset)

    # Update the line arrays from the newly computed invariants
    for idx in need_compute:
        rec = records[idx]
        a_lines[idx]      = str(rec.A)
        sig_lines[idx]    = str(int(rec.signature))
        jones_lines[idx]  = str(rec.jones_expr)
        casson_lines[idx] = str(rec.casson_dbc)

    # Write updated lists back to disk (including previously existing lines)
    a_path.write_text("\n".join(a_lines))
    sig_path.write_text("\n".join(sig_lines))
    jones_path.write_text("\n".join(jones_lines))
    casson_path.write_text("\n".join(casson_lines))
else:
    print("[Step 6] All HF-survivor classical invariants already present on disk.")

# At this point, every HF-survivor record has det, A, signature, jones_expr, casson_dbc.

# ---------------------------------------------------------------------
# Step 7: Casson test on HF-survivors -> final failList.txt
# ---------------------------------------------------------------------
print("[Step 7] Running Casson comparison on HF-surviving slopes...")
casson_log = run_casson_on_candidates(records, hf_candidates)

full_log = hf_log + casson_log
write_hf_outputs(BASE, records, full_log)
print("[Step 7] Casson comparison complete. failList.txt written.")

# ---------------------------------------------------------------------
# Step 8: Turaev–Viro comparison on Casson-survivors
# ---------------------------------------------------------------------
print("=== Step 8: Turaev–Viro comparison ===")
tv_ok = run_tv_compare(BASE)

if tv_ok:
    print("=== Fast pipeline complete ===")
else:
    print("=== Pipeline halted early in TV stage (slow cover); re-run to continue. ===")
