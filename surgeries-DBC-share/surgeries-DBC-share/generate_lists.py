import sys
from pathlib import Path

try:
    import snappy
except ImportError:
    print("CRITICAL ERROR: SnapPy is not installed.")
    print("Please run: mamba install -n sage snappy")
    sys.exit(1)

def numeric_to_alpha(dt_tuple):
    alpha_code = ""
    for val in dt_tuple:
        if val > 0:
            char_code = (val // 2) + 96
            alpha_code += chr(char_code)
        else:
            char_code = (abs(val) // 2) + 64
            alpha_code += chr(char_code)
    return alpha_code

def generate_lists(n):
    BASE = Path(".").resolve()
    
    name_file   = BASE / "knotList.txt"
    dt_file     = BASE / "DTList.txt"
    num_dt_file = BASE / "numDTList.txt"
    
    print(f"=== Generating Files for EXACTLY {n} crossings ===")
    
    with open(name_file, "w") as f_name, \
         open(dt_file, "w") as f_dt, \
         open(num_dt_file, "w") as f_num:
        try:
            if n <= 10:
                iterator = snappy.LinkExteriors(crossings=n)
            else:
                iterator = snappy.HTLinkExteriors(crossings=n)
            
            count = 0
            for knot in iterator:
                if knot.num_cusps() == 1:
                    name = knot.name()
                    if name.startswith("K") and n >= 11:
                        name = name[1:]
                    
                    raw_dt = knot.DT_code()
                    if len(raw_dt) > 0:
                        dt_tuple = raw_dt[0]
                        
                        alpha_dt = numeric_to_alpha(dt_tuple)
                        numeric_dt_str = ",".join(str(val) for val in dt_tuple)
                        
                        f_name.write(f"{name}\n")
                        f_dt.write(f"{alpha_dt}\n")
                        f_num.write(f"{numeric_dt_str}\n")
                        
                        count += 1
                        
                        if count % 1000 == 0:
                            print(f"  Processed {count} knots...", end="\r")
            
            print(f"\nSuccess! Generated lists for {count} knots with exactly {n} crossings.")
            
        except Exception as e:
            print(f"\nSTOPPED EARLY due to ERROR: {e}")

if __name__ == "__main__":
    N = 10
    generate_lists(N)