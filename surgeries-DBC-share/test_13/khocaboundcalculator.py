import subprocess
import re
import sys
import time
import resource

try:
    import spherogram
except ImportError:
    print("Error: The 'spherogram' library is required. pip install spherogram")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("Error: The 'tqdm' library is required. pip install tqdm")
    sys.exit(1)

def alphabet_to_dt_string(alpha_str):
    """Converts Knotscape alphabetical DT format into a numeric list."""
    dt_list = []
    for char in alpha_str.strip():
        if char.islower():
            val = (ord(char) - ord('a') + 1) * 2  # a=2, b=4, c=6
        elif char.isupper():
            val = -(ord(char) - ord('A') + 1) * 2 # A=-2, B=-4, C=-6
        else:
            continue
        dt_list.append(val)
    return str(dt_list)

def dt_to_khoca_pd(dt_string):
    """Converts a DT code string (alphabetical or numeric) into khoca's PD format."""
    dt_string = dt_string.strip()
    
    if dt_string.isalpha():
        dt_string = alphabet_to_dt_string(dt_string)
        
    if not dt_string.startswith('DT:'):
        dt_string = f"DT: {dt_string}"
        
    try:
        link = spherogram.Link(dt_string)
        pd_tuples = link.PD_code()
        pd_inner = ",".join(f"[{','.join(map(str, crossing))}]" for crossing in pd_tuples)
        return f"pd[{pd_inner}]"
    except Exception as e:
        return None

def parse_reduced_rank(khoca_output):
    """Parses khoca output to extract the absolute total rank of the Reduced Homology."""
    try:
        reduced_section = khoca_output.split("Unreduced Homology:")[0]
        
        poly_line = None
        for line in reduced_section.split('\n'):
            if 't^' in line and 'q^' in line:
                poly_line = line.strip()
                break
                
        if not poly_line:
            return "Error: Polynomial not found"

        rank = 0
        terms = poly_line.split('+')
        for term in terms:
            term = term.strip()
            match = re.match(r'^(\d*)t', term)
            if match:
                coef = match.group(1)
                rank += int(coef) if coef else 1
                
        return rank
    except Exception as e:
        return f"Error parsing: {e}"

def main():
    input_file = '/workspace/DTList.txt'
    output_file = '/workspace/HFBoundsKhoca.txt'
    profile_file = '/workspace/profiling.txt'
    
    # Pre-read lines so tqdm knows the total count for the progress bar
    try:
        with open(input_file, 'r') as f_in:
            lines = [line.strip() for line in f_in if line.strip()]
    except FileNotFoundError:
        print(f"Error: Could not find '{input_file}'.")
        sys.exit(1)
        
    print(f"Loaded {len(lines)} DT codes. Starting computations...\n")
    
    with open(output_file, 'w') as f_out, open(profile_file, 'w') as f_prof:
        # Set up the profiling log header
        f_prof.write("Knot_Code | Time_Taken(s) | Peak_Child_Memory(MB)\n")
        f_prof.write("-" * 55 + "\n")
        
        # Track total global time
        global_start_time = time.time()
        
        # tqdm automatically handles the progress bar in the terminal
        for raw_code in tqdm(lines, desc="Processing Knots", unit="knot"):
            
            # Start knot-specific timer
            knot_start_time = time.time()
            
            pd_code = dt_to_khoca_pd(raw_code)
            if not pd_code:
                f_out.write(f"{raw_code} | Error: Invalid DT conversion\n")
                f_prof.write(f"{raw_code} | N/A | N/A (Conversion Failed)\n")
                continue
            
            cmd = ["./khoca.py", "2", "0.0", "0", pd_code, "calc0"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Calculate elapsed time for this specific knot
            knot_elapsed = time.time() - knot_start_time
            
            # Ask the OS kernel for the max memory used by child processes so far
            # Note: ru_maxrss is returned in Kilobytes on Linux
            child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            peak_memory_mb = child_usage.ru_maxrss / 1024.0
            
            if result.returncode != 0:
                f_out.write(f"{raw_code} | Error: khoca execution failed\n")
                f_prof.write(f"{raw_code} | {knot_elapsed:.4f} | {peak_memory_mb:.2f} (Khoca Crash)\n")
                continue
            
            rank = parse_reduced_rank(result.stdout)
            f_out.write(f"{rank}\n")
            
            # Log the profiling data
            f_prof.write(f"{raw_code} | {knot_elapsed:.4f} | {peak_memory_mb:.2f}\n")
            
        # Final global metrics
        global_elapsed = time.time() - global_start_time
        final_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        final_peak_memory_mb = final_usage.ru_maxrss / 1024.0
        
        f_prof.write("-" * 55 + "\n")
        f_prof.write(f"TOTAL TIME: {global_elapsed:.2f} seconds\n")
        f_prof.write(f"ABSOLUTE PEAK MEMORY: {final_peak_memory_mb:.2f} MB\n")
            
    print(f"\nAll done! Bounds saved to {output_file}")
    print(f"Profiling data saved to {profile_file}")

if __name__ == "__main__":
    main()