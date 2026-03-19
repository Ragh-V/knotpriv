import sys
from pathlib import Path

# Attempt to import SnapPy
try:
    import snappy
except ImportError:
    print("CRITICAL ERROR: SnapPy is not installed.")
    print("Please run: mamba install -n sage snappy")
    sys.exit(1)

def numeric_to_alpha(dt_tuple):
    """
    Converts a SnapPy numeric DT tuple (e.g. [4, -6, 8]) 
    to the alphabetical string format (e.g. "bC d...").
    """
    alpha_code = ""
    for val in dt_tuple:
        if val > 0:
            # Lowercase logic (2 -> 'a', 4 -> 'b')
            char_code = (val // 2) + 96
            alpha_code += chr(char_code)
        else:
            # Uppercase logic (-2 -> 'A', -4 -> 'B')
            char_code = (abs(val) // 2) + 64
            alpha_code += chr(char_code)
            
    return alpha_code

def generate_lists(n):
    # 1. Setup paths
    BASE = Path(".").resolve()
    # You can rename these if you want specific filenames like "knotList_16.txt"
    name_file = BASE / "knotList.txt"
    dt_file   = BASE / "DTList.txt"
    
    print(f"=== Generating Files for EXACTLY {n} crossings ===")
    print(f"1. Names:   {name_file}")
    print(f"2. DT Codes:{dt_file}")
    print("-" * 50)
    
    # Open both files
    with open(name_file, "w") as f_name, open(dt_file, "w") as f_dt:
        try:
            # Select census: Rolfsen (<=10) or Hoste-Thistlethwaite (>=11)
            if n <= 10:
                print(f"Using Rolfsen table for n={n}...")
                iterator = snappy.LinkExteriors(crossings=n)
            else:
                print(f"Using Hoste-Thistlethwaite census for n={n}...")
                iterator = snappy.HTLinkExteriors(crossings=n)
            
            count = 0
            for knot in iterator:

                if knot.num_cusps() == 1:
                    

                    name = knot.name()
                    # Clean knot name if starting with K
                    if name.startswith("K") and n >= 11:
                        name = name[1:]
                    

                    raw_dt = knot.DT_code()
                    if len(raw_dt) > 0:
                        alpha_dt = numeric_to_alpha(raw_dt[0])
                        
                        # Write to files
                        f_name.write(f"{name}\n")
                        f_dt.write(f"{alpha_dt}\n")
                        
                        count += 1
                        

                        if count % 10000 == 0:
                            print(f"  Processed {count} knots...", end="\r")
            
            print(f"\KnotList and DTList populated with {count} knots with exactly {n} crossings.")
            
        except Exception as e:
            print(f"\nSTOPPED EARLY due to ERROR: {e}")
            if n >= 15:
                print("-" * 60)
                print("please run pip install snappy_15_knots snappy_16_knots")
                print("-" * 60)

if __name__ == "__main__":

    N = 14
    generate_lists(N)