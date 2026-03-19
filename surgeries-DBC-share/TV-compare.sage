# TV-compare.sage
#
# Driver script: run the Turaev–Viro comparison using surgeries_dbc.tv_compare.

import sys
from pathlib import Path

# repo root is mounted at /repo in the Docker command
sys.path.append("/repo")

from surgeries_dbc.tv_compare import run_tv_compare

BASE = Path("/work").resolve()

print("Running Turaev–Viro comparison...")
run_tv_compare(BASE)
print("Done.")
