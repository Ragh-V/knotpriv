import sys
import yaml
import time
from pathlib import Path

from surgeries_dbc.io import (
    load_knot_records,
    write_classical_lists,
    load_classical_lists,
    write_hf_outputs,
)


# 1. SETUP PATHS
# Use the current directory where you launch the script
BASE = Path.cwd().resolve()
fail_list_path = BASE / "failList.txt"

# Update this to the actual path where your 'surgeries_dbc' folder lives
# If it's in the same folder as this script, you can use BASE
REPO_PATH = "/path/to/your/repo" 
sys.path.append(REPO_PATH)

try:
    from surgeries_dbc.io import (
        load_knot_records,
        write_classical_lists,
        load_classical_lists,
    )
    from surgeries_dbc.invariants import compute_classical_invariants
    from surgeries_dbc.hf_casson import attach_hf_data, run_hf_casson
    from surgeries_dbc.tv_compare import run_tv_compare
except ImportError as e:
    print(f"Error: Could not import surgeries_dbc modules. Check REPO_PATH.\n{e}")
    sys.exit(1)

print(f"--- Pipeline Initialized in: {BASE} ---")

# ---------------------------------------------------------------------
# Stage 0: Fast Path Check
# ---------------------------------------------------------------------
if fail_list_path.exists() and fail_list_path.stat().st_size > 0:
    print("=== Fast path: failList.txt found, running Turaev–Viro only ===")
    tv_ok = run_tv_compare(BASE)
    print("=== Turaev–Viro stage complete ===" if tv_ok else "=== TV Halted Early ===")
    sys.exit(0)

# ---------------------------------------------------------------------
# Stage 1: DT conversion (Pure Numeric - No Prefix, No Brackets)
# ---------------------------------------------------------------------
print("=== Stage 1: DT conversion ===")
dt_alpha_path = BASE / "DTList.txt"
num_dt_path   = BASE / "numDTList.txt"

if num_dt_path.exists():
    print(f"{num_dt_path.name} already exists; skipping.")
else:
    if not dt_alpha_path.exists():
        print(f"Error: {dt_alpha_path.name} not found. Cannot proceed.")
        sys.exit(1)
        
    numeric_lines = []
    with open(dt_alpha_path, 'r') as f:
        for line in f:
            code = line.strip()
            if not code:
                continue
            
            converted_vals = []
            for char in code:
                # Lowercase (a=2, b=4...) | Uppercase (A=-2, B=-4...)
                if ord(char) > 95:
                    val = 2 * (ord(char) - 96)
                else:
                    val = -2 * (ord(char) - 64)
                converted_vals.append(str(val))
            
            # Outputs: -10,-8,-12,-14,-2,-4,-6
            numeric_lines.append(",".join(converted_vals))

    with open(num_dt_path, 'w') as f:
        f.write("\n".join(numeric_lines) + "\n")
    
    print(f"Successfully created {num_dt_path.name} in raw format.")
# ---------------------------------------------------------------------
# Stage 2: Classical Invariants
# ---------------------------------------------------------------------
print("=== Stage 2: Classical invariants ===")
records = load_knot_records(BASE)

# Check if all 5 classical lists exist
needed = ["detList.txt", "aList.txt", "sigList.txt", "jonesList.txt", "cassonList.txt"]
have_classical = all((BASE / p).exists() for p in needed)

if have_classical:
    print("Loading existing classical invariant lists.")
    load_classical_lists(BASE, records)
else:
    print("Computing classical invariants (det, A, sig, Jones, Casson)...")
    compute_classical_invariants(records)
    write_classical_lists(BASE, records)

# ---------------------------------------------------------------------
# Stage 3: HF + Casson Comparison (With YAML & Profiling)
# ---------------------------------------------------------------------
print("=== Stage 3: HF + Casson comparison ===")

attach_hf_data(BASE, records)

# Timing the whole stage
t3_start = time.perf_counter()
yaml_data, profile_lines, fail_list = run_hf_casson(records)
t3_elapsed = time.perf_counter() - t3_start

# Save YAML Results
with open(BASE / "hf_casson_results.yaml", "w") as f_yaml:
    yaml.dump(yaml_data, f_yaml, sort_keys=False, default_flow_style=False)

# Save Profiling Data
with open(BASE / "profiling_hf_casson.txt", "w") as f_prof:
    f_prof.write("Knot_Name | HF_Time(s) | Casson_Time(s) | Total_Time(s)\n")
    f_prof.write("-" * 65 + "\n")
    f_prof.write("\n".join(profile_lines) + "\n")
    f_prof.write("-" * 65 + "\n")
    f_prof.write(f"Total Stage 3 Time: {t3_elapsed:.4f} s\n")



if fail_list_path.exists():
    print("failList.txt already exists; skipping HF + Casson stage.")
else:
    print("failList.txt not found; running HF + Casson comparison...")
    attach_hf_data(BASE, records)
    output_log = run_hf_casson(records)
    write_hf_outputs(BASE, records, str(output_log))

print(f"Stage 3 Complete. {len(fail_list)} knots queued for TV.")

# ---------------------------------------------------------------------
# Stage 4: Turaev–Viro Comparison
# ---------------------------------------------------------------------
print("=== Stage 4: Turaev–Viro comparison ===")
tv_ok = run_tv_compare(BASE)
print("=== Pipeline Complete ===" if tv_ok else "=== TV Halted Early ===")