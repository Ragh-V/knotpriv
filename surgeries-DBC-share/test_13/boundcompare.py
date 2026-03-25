import sys

def compare_bounds():
    # Define the file names (make sure these match exactly)
    hf_file = 'HFboundList.txt'
    khoca_file = 'HFBoundsKhoca.txt'
    dt_file = 'DTList.txt'

    try:
        # Open all three files simultaneously
        with open(hf_file, 'r') as f_hf, \
             open(khoca_file, 'r') as f_kh, \
             open(dt_file, 'r') as f_dt:
            
            hf_lines = f_hf.readlines()
            khoca_lines = f_kh.readlines()
            dt_lines = f_dt.readlines()
            
    except FileNotFoundError as e:
        print(f"Error: Could not find one of the files. {e}")
        sys.exit(1)

    # Sanity check: Ensure all files have the same number of lines
    if not (len(hf_lines) == len(khoca_lines) == len(dt_lines)):
        print("Warning: The files do not have the same number of lines!")
        print(f"Lines -> HFboundList: {len(hf_lines)}, HFBoundsKhoca: {len(khoca_lines)}, DTList: {len(dt_lines)}\n")

    discrepancy_found = False

    # zip() lets us iterate through all three lists at the same time
    for i, (hf, kh, dt) in enumerate(zip(hf_lines, khoca_lines, dt_lines), start=1):
        hf_val = hf.strip()
        kh_val = kh.strip()
        dt_code = dt.strip()

        # Skip completely empty lines to avoid false positives
        if not dt_code and not hf_val and not kh_val:
            continue

        # Compare the values
        if hf_val != kh_val:
            discrepancy_found = True
            print(f"Discrepancy found | Knot: {dt_code}")
            print(f"  -> Pre-existing (HFboundList): {hf_val}")
            print(f"  -> Khoca computed:             {kh_val}\n")

    # If the loop finishes and the flag is still False, we have a perfect match
    if not discrepancy_found:
        print("No discrepancies between pre-existing bounds and khoca bounds.")

if __name__ == "__main__":
    compare_bounds()