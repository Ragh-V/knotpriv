import subprocess
import re
import sys

try:
    import spherogram
except ImportError:
    print("Error: The 'spherogram' library is required to convert DT codes to PD codes.")
    print("Please install it by running: pip install spherogram")
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
    
    # 1. If the input is alphabetical (e.g., 'EDFGABC'), translate it to numbers first
    if dt_string.isalpha():
        dt_string = alphabet_to_dt_string(dt_string)
        
    # 2. Ensure spherogram recognizes it as a DT code
    if not dt_string.startswith('DT:'):
        dt_string = f"DT: {dt_string}"
        
    try:
        # Generate the Link object and get its PD code
        link = spherogram.Link(dt_string)
        pd_tuples = link.PD_code()
        
        # Format it exactly as khoca expects: pd[[4,2,5,1],...]
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
    # Using absolute paths to ensure Docker finds the files in the mounted volume
    input_file = '/workspace/DTList.txt'
    output_file = '/workspace/HFBoundsKhoca.txt'
    
    print(f"Reading DT codes from {input_file}...\n")
    
    try:
        with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
            for line_num, line in enumerate(f_in, 1):
                raw_code = line.strip()
                if not raw_code:
                    continue
                
                print(f"[{line_num}] Processing: {raw_code}")
                
                pd_code = dt_to_khoca_pd(raw_code)
                if not pd_code:
                    print(f"  -> Failed to convert to PD.")
                    f_out.write(f"{raw_code} | Error: Invalid DT conversion\n")
                    continue
                
                # Execute khoca directly
                cmd = ["./khoca.py", "2", "0.0", "0", pd_code, "calc0"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"  -> khoca crashed.")
                    f_out.write(f"{raw_code} | Error: khoca execution failed\n")
                    continue
                
                rank = parse_reduced_rank(result.stdout)
                print(f"  -> Reduced Rank: {rank}")
                f_out.write( f"{rank}\n")
                
        print(f"\nAll done! Results saved to {output_file}.")
        
    except FileNotFoundError:
        print(f"Error: Could not find '{input_file}'.")

if __name__ == "__main__":
    main()