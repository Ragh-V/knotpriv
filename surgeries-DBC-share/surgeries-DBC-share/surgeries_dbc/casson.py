import sys
import json
from pathlib import Path
from typing import List, Dict, Any

sys.path.append("/repo")

from surgeries_dbc.io import load_knot_records
from surgeries_dbc.invariants import compute_classical_invariants
from surgeries_dbc.models import KnotRecord

def run_export(base_dir: Path, output_file: Path):
    records = load_knot_records(base_dir)

    if not records:
        print("No records found. Check if numDTList.txt exists in /work.")
        return

    print(f"Loaded {len(records)} records.")

    compute_classical_invariants(records)

    export_data: List[Dict[str, Any]] = []
    i = 1
    for rec in records:
        i += 1 
        if i %100 == 0:
            print(f"Computed {i} records!")
        casson_str = str(rec.casson_dbc)

        entry = {
            "dt_numeric": rec.dt_numeric,
            "dt_alpha": rec.dt_alpha,
            "casson_dbc": casson_str,
            "signature": int(rec.signature),
            "det": int(rec.det)
        }
        export_data.append(entry)

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print("Done.")

if __name__ == "__main__":
    BASE_WORK_DIR = Path("/work").resolve()
    OUTPUT_JSON = BASE_WORK_DIR / "knots_casson.json"

    run_export(BASE_WORK_DIR, OUTPUT_JSON)