# run_pipeline.sage
#
# One-shot pipeline with incremental behavior:
#   0. Fast path: if failList.txt exists, run only Turaev–Viro and exit.
#   1. DT-convert.sage        (generate numDTList.txt)      [skips if present]
#   2. Classical invariants   (det, A, sig, Jones, Casson)  [skips compute if lists present]
#   3. HF + Casson compare    (Casson-comparison, failList) [skips if failList.txt present]
#   4. Turaev–Viro compare    (whatsLeft, progress, exceptions) [resumable]
#
# Assumes:
#   - data directory is /work (mounted from the test_x-y folder)
#   - repo root (with surgeries_dbc/) is /repo

import sys
from pathlib import Path

sys.path.append("/repo")

from surgeries_dbc.io import (
    load_knot_records,
    write_classical_lists,
    load_classical_lists,
    write_hf_outputs,
)
from surgeries_dbc.invariants import compute_classical_invariants
from surgeries_dbc.hf_casson import attach_hf_data, run_hf_casson
from surgeries_dbc.tv_compare import run_tv_compare

BASE = Path("/work").resolve()
fail_list_path = BASE / "failList.txt"

# ---------------------------------------------------------------------
# Fast path: if failList.txt exists, just run TV and exit
# ---------------------------------------------------------------------

if fail_list_path.exists():
    print("=== Fast path: failList.txt found, skipping stages 1–3 and running Turaev–Viro only ===")
    tv_ok = run_tv_compare(BASE)
    if tv_ok:
        print("=== Turaev–Viro stage complete ===")
    else:
        print("=== Turaev–Viro stage halted early due to slow cover; re-run to continue. ===")
    sys.exit(0)

# ---------------------------------------------------------------------
# Stage 1: DT conversion (numDTList.txt)
# ---------------------------------------------------------------------

print("=== Stage 1: DT conversion ===")
num_dt_path = BASE / "numDTList.txt"

if num_dt_path.exists():
    print("numDTList.txt already exists; skipping DT-convert.sage.")
else:
    print("numDTList.txt not found; running DT-convert.sage...")
    load("/repo/DT-convert.sage")

# ---------------------------------------------------------------------
# Stage 2: Classical invariants (det, A, sig, Jones, Casson)
# ---------------------------------------------------------------------

print("=== Stage 2: Classical invariants ===")
records = load_knot_records(BASE)

det_path    = BASE / "detList.txt"
a_path      = BASE / "aList.txt"
sig_path    = BASE / "sigList.txt"
jones_path  = BASE / "jonesList.txt"
casson_path = BASE / "cassonList.txt"

have_classical = all(
    p.exists() for p in [det_path, a_path, sig_path, jones_path, casson_path]
)

if have_classical:
    print("Classical invariant lists already exist; loading from files.")
    load_classical_lists(BASE, records)
else:
    print("Classical invariant lists missing; computing from scratch...")
    compute_classical_invariants(records)
    write_classical_lists(BASE, records)

# At this point, `records` has det, A, signature, Jones, casson_dbc populated.

# ---------------------------------------------------------------------
# Stage 3: HF + Casson comparison
# ---------------------------------------------------------------------

print("=== Stage 3: HF + Casson comparison ===")

if fail_list_path.exists():
    print("failList.txt already exists; skipping HF + Casson stage.")
else:
    print("failList.txt not found; running HF + Casson comparison...")
    attach_hf_data(BASE, records)
    output_log = run_hf_casson(records)
    write_hf_outputs(BASE, records, output_log)

# ---------------------------------------------------------------------
# Stage 4: Turaev–Viro comparison
# ---------------------------------------------------------------------

print("=== Stage 4: Turaev–Viro comparison ===")
tv_ok = run_tv_compare(BASE)

if tv_ok:
    print("=== Pipeline complete ===")
else:
    print("=== Pipeline halted early during Turaev–Viro stage due to slow cover; re-run to continue. ===")
