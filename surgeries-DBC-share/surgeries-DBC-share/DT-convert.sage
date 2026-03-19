# DT-convert.sage
#
# Run this in a directory that contains DTList.txt.
# It reads DTList.txt (alphabetical DT codes) and writes numDTList.txt (numeric codes)
# in the same directory.

from pathlib import Path

# 1. Change BASE to the current directory
BASE = Path(".").resolve()

# Input and output files
DT_LIST     = BASE / "DTList.txt"
NUM_DT_LIST = BASE / "numDTList.txt"


def DTconvert(dt):
    """
    Convert an alphabetical Dowker–Thistlethwaite code (one line of text)
    to a comma-separated numeric code.
    """
    new_dt = ""
    # Strip whitespace/newlines to avoid parsing errors
    dt = dt.strip()
    
    for x in dt:
        if ord(x) > 95:          # lowercase letters
            y = 2 * (ord(x) - 96)
        else:                      # uppercase letters
            y = -2 * (ord(x) - 64)
        new_dt += f"{y},"

    # Remove trailing comma
    return new_dt.rstrip(",")




if not DT_LIST.exists():
    print(f"Error: {DT_LIST} not found in the current directory.")
else:
    # Read all DT codes, one per line
    with DT_LIST.open("r") as f:
        DTList = [line for line in f if line.strip()]

    # Convert each code
    numDTList = [DTconvert(dt) for dt in DTList]

    # Write the numeric codes, one per line
    with NUM_DT_LIST.open("w") as f:
        f.write("\n".join(numDTList))
    
    print(f"Successfully converted {len(numDTList)} codes to numDTList.txt")