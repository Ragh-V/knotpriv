# HF-Casson-compare.sage
#
# Driver script: load knots + classical invariants from lists, attach HF data,
# run HF + Casson comparison, and write logs.

import sys
from pathlib import Path

sys.path.append("/repo")

from surgeries_dbc.io import (
    load_knot_records,
    load_classical_lists,
    write_hf_outputs,
)
from surgeries_dbc.hf_casson import attach_hf_data, run_hf_casson

BASE = Path("/work").resolve()

print("Loading knots...")
records = load_knot_records(BASE)

print("Loading classical invariants from lists...")
load_classical_lists(BASE, records)

print("Attaching HF data (m, n, HFbound)...")
attach_hf_data(BASE, records)

print("Running HF + Casson comparison...")
output_log = run_hf_casson(records)

print("Writing HF outputs...")
write_hf_outputs(BASE, records, output_log)

print("Done.")
