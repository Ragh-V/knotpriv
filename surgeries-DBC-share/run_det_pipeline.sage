# run_det_pipeline.sage
#
# Minimal pipeline:
#   - Ensure numDTList.txt exists (run DT-convert.sage if needed)
#   - Load KnotRecord list
#   - Compute det(K) for each knot
#   - Write detList.txt

import sys
from pathlib import Path

sys.path.append("/repo")

from surgeries_dbc.io import load_knot_records
from surgeries_dbc.invariants_det_only import compute_determinants

BASE = Path("/work").resolve()
num_dt_path = BASE / "numDTList.txt"
det_path = BASE / "detList.txt"

print("=== Determinant-only pipeline ===")

# ---------------------------------------------------------------------
# Step 1: Ensure numDTList.txt exists
# ---------------------------------------------------------------------

if num_dt_path.exists():
    print("numDTList.txt already exists; using existing numeric DT codes.")
else:
    print("numDTList.txt not found; running DT-convert.sage...")
    load("/repo/DT-convert.sage")

# ---------------------------------------------------------------------
# Step 2: Load knot records (name, DTList, numDTList)
# ---------------------------------------------------------------------

print("Loading knot records from:", BASE)
records = load_knot_records(BASE)
print(f"Loaded {len(records)} knots.")

# ---------------------------------------------------------------------
# Step 3: Compute determinants
# ---------------------------------------------------------------------

print("Computing determinants det(K) = |Δ_K(-1)| ...")
compute_determinants(records)

# ---------------------------------------------------------------------
# Step 4: Write detList.txt
# ---------------------------------------------------------------------

print("Writing detList.txt ...")
det_lines = [str(rec.det) for rec in records]
det_path.write_text("\n".join(det_lines))

print("Done. detList.txt written to", det_path)
