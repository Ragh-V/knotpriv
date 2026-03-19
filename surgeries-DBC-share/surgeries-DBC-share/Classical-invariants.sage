# Classical-invariants.sage
#
# Driver script: load knots, compute classical invariants using
# surgeries_dbc, and write the traditional text files.

import sys
from pathlib import Path

# Make sure the repo root (with surgeries_dbc/) is on sys.path.
# We mounted it at /repo in the docker command.
sys.path.append("/repo")

from surgeries_dbc.io import load_knot_records, write_classical_lists
from surgeries_dbc.invariants import compute_classical_invariants

BASE = Path("/work").resolve()

print("Loading knots...")
records = load_knot_records(BASE)

print("Computing classical invariants...")
compute_classical_invariants(records)

print("Writing classical invariant lists...")
write_classical_lists(BASE, records)

print("Done.")
