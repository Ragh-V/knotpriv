# run_tv_only.sage
#
# Only run the Turaev–Viro comparison stage, assuming:
#   - /work contains failList.txt, whatsLeft.txt, progress.txt, etc
#   - /repo contains surgeries_dbc/ and tv_compare.py

import sys
from pathlib import Path

sys.path.append("/repo")

from surgeries_dbc.tv_compare import run_tv_compare

BASE = Path("/work").resolve()

print("=== TV-only stage ===")
tv_ok = run_tv_compare(BASE)

if tv_ok:
    print("=== TV-only stage complete (no remaining slopes) ===")
else:
    print("=== TV-only stage halted early (slow cover); re-run this script to continue. ===")
