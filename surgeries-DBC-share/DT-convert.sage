# DT-convert.sage
#
# Run this in a directory that contains DTList.txt.
# It reads DTList.txt (alphabetical DT codes) and writes numDTList.txt (numeric codes)
# in the same directory.

from pathlib import Path

# Base directory for all files in this run (inside Docker this will be /work)
BASE = Path("/work").resolve()

# Input and output files
DT_LIST     = BASE / "DTList.txt"
NUM_DT_LIST = BASE / "numDTList.txt"


def DTconvert(dt):
    """
    Convert an alphabetical Dowker–Thistlethwaite code (one line of text)
    to a comma-separated numeric code.
    """
    new_dt = ""
    for x in dt:
        if x == "\n":
            continue
        elif ord(x) > 95:          # lowercase letters
            y = 2 * (ord(x) - 96)
        else:                      # uppercase letters
            y = -2 * (ord(x) - 64)
        new_dt += f"{y},"

    # Remove trailing comma, if any
    if new_dt.endswith(","):
        new_dt = new_dt[:-1]

    return new_dt


# --- main script body ---

# Read all DT codes, one per line
with DT_LIST.open("r") as f:
    DTList = f.readlines()

# Convert each code
numDTList = [DTconvert(dt) for dt in DTList]

# Write the numeric codes, one per line
with NUM_DT_LIST.open("w") as f:
    f.write("\n".join(numDTList))
