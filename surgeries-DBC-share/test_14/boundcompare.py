import sys

def compare_bounds():
    # Define the file names
    hf_file = 'HFboundList.txt'
    khoca_file = 'HFBoundsKhoca.txt'
    dt_file = 'DTList.txt'
    output_file = 'discrepancies.txt'

    try:
        with open(hf_file, 'r') as f_hf, \
             open(khoca_file, 'r') as f_kh, \
             open(dt_file, 'r') as f_dt:
            
            hf_lines = [line.strip() for line in f_hf]
            khoca_lines = [line.strip() for line in f_kh]
            dt_lines = [line.strip() for line in f_dt]
            
    except FileNotFoundError as e:
        print(f"Error: Could not find one of the files. {e}")
        sys.exit(1)

    # Statistics Tracking
    total_lines = len(hf_lines)
    mismatches = []
    match_count = 0

    # Iterate and compare
    for i, (hf_val, kh_val, dt_code) in enumerate(zip(hf_lines, khoca_lines, dt_lines)):
        # Skip empty lines
        if not dt_code and not hf_val and not kh_val:
            total_lines -= 1 # Adjust total if skipping empty rows
            continue

        if hf_val != kh_val:
            mismatches.append({
                'knot': dt_code,
                'hf': hf_val,
                'khoca': kh_val
            })
        else:
            match_count += 1

    # Write results to the file
    with open(output_file, 'w') as f_out:
        # Header Section
        f_out.write("========================================\n")
        f_out.write("          COMPARISON SUMMARY            \n")
        f_out.write("========================================\n")
        f_out.write(f"Total Lines Processed: {total_lines}\n")
        f_out.write(f"Number of Matches:     {match_count}\n")
        f_out.write(f"Number of Mismatches:  {len(mismatches)}\n")
        f_out.write("========================================\n\n")

        # Discrepancy Details
        if not mismatches:
            f_out.write("No discrepancies found. All values match perfectly.\n")
        else:
            f_out.write("DETAILED DISCREPANCIES:\n")
            f_out.write("-----------------------\n")
            for m in mismatches:
                f_out.write(f"Knot: {m['knot']}\n")
                f_out.write(f"  -> Pre-existing: {m['hf']}\n")
                f_out.write(f"  -> Khoca:        {m['khoca']}\n\n")

    print(f"Comparison complete. {len(mismatches)} mismatches found.")
    print(f"Results written to: {output_file}")

if __name__ == "__main__":
    compare_bounds()