# run_casson_only.sage
#
# Casson-only pipeline USING PRECOMPUTED CLASSICAL INVARIANTS.
#
# Assumes the following files already exist in /work:
#   - knotList.txt, DTList.txt, numDTList.txt
#   - detList.txt                    (det(K))
#   - mList.txt, nList.txt, HFboundList.txt
#   - aList.txt, sigList.txt, jonesList.txt, cassonList.txt
#
# This script:
#   1. Loads knot records.
#   2. Loads det(K) from detList.txt.
#   3. Attaches HF data (m, n, HFbound).
#   4. Runs the HF-only filter -> hf_candidates, hf_failList.txt.
#   5. Loads A(K), signature, Jones, Casson(DBC) ONLY for HF-survivors.
#   6. Runs Casson comparison on HF-surviving slopes, writing:
#        - Casson-comparison-results.txt
#        - failList.txt (post-Casson survivors).

import sys
from pathlib import Path

import sympy as sym

sys.path.append("/repo")

from surgeries_dbc.io import load_knot_records, write_hf_outputs
from surgeries_dbc.hf_casson import attach_hf_data
from surgeries_dbc.hf_filter import hf_filter, write_hf_fail_list
from surgeries_dbc.casson_only import run_casson_on_candidates

BASE = Path("/work").resolve()

print("=== Casson-only pipeline (using precomputed classical invariants) ===")

# ---------------------------------------------------------------------
# Step 1: Load knot records (names + DT codes)
# ---------------------------------------------------------------------
print("[Step 1] Loading knot records...")
records = load_knot_records(BASE)
n_knots = len(records)
print(f"[Step 1] Loaded {n_knots} knots.")

# ---------------------------------------------------------------------
# Step 2: Load determinants det(K) from detList.txt
# ---------------------------------------------------------------------
det_path = BASE / "detList.txt"
if not det_path.exists():
    raise FileNotFoundError(f"detList.txt not found in {BASE}")

det_lines = det_path.read_text().splitlines()
if len(det_lines) != n_knots:
    raise ValueError(
        f"detList.txt length {len(det_lines)} does not match "
        f"number of records {n_knots}."
    )

for rec, d_s in zip(records, det_lines):
    rec.det = int(d_s.strip())

print("[Step 2] Determinants loaded from detList.txt.")

# ---------------------------------------------------------------------
# Step 3: Attach HF data (m, n, HFbound)
# ---------------------------------------------------------------------
print("[Step 3] Attaching HF data (m, n, HFbound) from mList/nList/HFboundList...")
attach_hf_data(BASE, records)
print("[Step 3] HF data attached.")

# ---------------------------------------------------------------------
# Step 4: HF-only filter -> hf_candidates, hf_failList.txt
# ---------------------------------------------------------------------
print("[Step 4] Running HF-only filter...")
hf_log, hf_candidates = hf_filter(records)
write_hf_fail_list(BASE, records, hf_candidates)

if not hf_candidates:
    print("[Step 4] HF obstruction ruled out all slopes; Casson check not needed.")
    # Write empty failList.txt to signal "no Casson/TV survivors".
    (BASE / "failList.txt").write_text("")
    print("=== Casson-only pipeline complete (no Casson survivors). ===")
    sys.exit(0)

print(f"[Step 4] HF-surviving knots: {len(hf_candidates)}")

# ---------------------------------------------------------------------
# Step 5: Load classical invariants ONLY for HF-survivors
# ---------------------------------------------------------------------
print("[Step 5] Loading classical invariants from aList/sigList/jonesList/cassonList "
      "for HF-survivors only...")

a_path      = BASE / "aList.txt"
sig_path    = BASE / "sigList.txt"
jones_path  = BASE / "jonesList.txt"
casson_path = BASE / "cassonList.txt"

def _load_list_or_die(path: Path, n: int) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"{path.name} not found in {BASE}")
    lines = path.read_text().splitlines()
    if len(lines) != n:
        raise ValueError(
            f"{path.name} length {len(lines)} does not match number of records {n}."
        )
    return lines

# Read the full lists once (cheap); only parse HF-survivor entries.
a_lines      = _load_list_or_die(a_path, n_knots)
sig_lines    = _load_list_or_die(sig_path, n_knots)
jones_lines  = _load_list_or_die(jones_path, n_knots)
casson_lines = _load_list_or_die(casson_path, n_knots)

hf_indices = sorted(hf_candidates.keys())
total_survivors = len(hf_indices)

# Attach classical invariants only for HF-surviving indices, with progress
for count, idx in enumerate(hf_indices, start=1):
    rec = records[idx]
    a_s    = a_lines[idx].strip()
    sig_s  = sig_lines[idx].strip()
    j_s    = jones_lines[idx].strip()
    cass_s = casson_lines[idx].strip()

    if a_s == "" or sig_s == "" or j_s == "" or cass_s == "":
        raise ValueError(f"Missing classical invariant data for record {rec.name} at index {idx}")

    rec.A          = sym.sympify(a_s)
    rec.signature  = int(sig_s)
    rec.jones_expr = sym.sympify(j_s)
    rec.casson_dbc = sym.sympify(cass_s)

    # Progress update every 2000 HF-survivors (and at the end)
    if count % 2000 == 0 or count == total_survivors:
        print(f"[Step 5] Attached invariants for {count} / {total_survivors} HF-survivors")

print("[Step 5] Classical invariants attached for all HF-survivors.")

# ---------------------------------------------------------------------
# Step 6: Casson comparison on HF-survivors -> final failList.txt
# ---------------------------------------------------------------------
print("[Step 6] Running Casson comparison on HF-surviving slopes...")
casson_log = run_casson_on_candidates(records, hf_candidates)

full_log = hf_log + casson_log
write_hf_outputs(BASE, records, full_log)

print("[Step 6] Casson comparison complete.")
print("  - Casson-comparison-results.txt written.")
print("  - failList.txt written (post-Casson survivors).")
print("=== Casson-only pipeline complete ===")
