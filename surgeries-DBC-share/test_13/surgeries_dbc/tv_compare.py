# surgeries_dbc/tv_compare.py
#
# Turaev–Viro comparison stage, factored into a library function.
# It reads failList.txt (from HF-Casson-compare), maintains
# whatsLeft.txt, progress.txt, and exceptions.txt, and computes
# T-V invariants for the DBC and p/q surgeries.
#
# Behavior mirrors your later standalone script, including:
#   - a maxtime cutoff on the cover's T-V computation
#   - extra simplify() calls
#   - exceptions.txt for slopes where T-V fails to distinguish
#   - semantics: whatsLeft tracks slopes not yet PROCESSED at all.
#
# The manifold is constructed via DTList[k] (DT description).

from pathlib import Path
import copy
import time

import snappy
import regina


def run_tv_compare(base: Path, maxtime: float = .5) -> bool:
    """
    Run the Turaev–Viro comparison for the dataset in `base`.

    Expects:
      - failList.txt   (from HF-Casson-compare)

    Maintains:
      - whatsLeft.txt   : working list of remaining (knot, p, q's) to process
      - progress.txt    : human-readable progress log
      - exceptions.txt  : cases where T-V fails to distinguish (tvSurgery == tvCover)

    Behavior:
      - If whatsLeft.txt does not exist, it is initialized from failList.txt.
      - If exceptions.txt does not exist, it is created empty.
      - For each knot with remaining slopes:
          * computes T-V of the double branched cover
            (via a 2-fold cover and Dehn filling)
            with a time limit maxtime on that computation.
          * computes T-V of all p/q surgeries listed for that knot.
          * removes each processed q from whatsLeft, regardless of success;
            failures are recorded in exceptions.txt.

    Returns:
      - True  if all remaining knots were processed without hitting the maxtime cutoff.
      - False if the run aborted early because the cover was too slow.
    """
    FAIL_LIST   = base / "failList.txt"
    WHATSLEFT   = base / "whatsLeft.txt"
    PROGRESS    = base / "progress.txt"
    EXCEPTIONS  = base / "exceptions.txt"

    if not FAIL_LIST.exists() and not WHATSLEFT.exists():
        raise FileNotFoundError("failList.txt or whatsLeft.txt not found; run HF-Casson-compare first.")

    # Initialize whatsLeft.txt from failList.txt on first run.
    if not WHATSLEFT.exists():
        with FAIL_LIST.open("r") as firstfile, WHATSLEFT.open("w") as secondfile:
            for line in firstfile:
                print(f"copying {line.strip()} to whatsLeft.txt")
                secondfile.write(line)

    # Initialize exceptions.txt if needed.
    if not EXCEPTIONS.exists():
        EXCEPTIONS.write_text("")

    # Load the current working list.
    with WHATSLEFT.open("r") as f:
        whatsLeftPrevious = f.readlines()

    # Load existing exceptions.
    with EXCEPTIONS.open("r") as f:
        exceptions = f.readlines()

    knotList = []
    DTList   = []
    pList    = []
    qList    = []

    whatsLeft: list[str] = []

    for x in whatsLeftPrevious:
        if x != "Done!\n":
            whatsLeft.append(copy.deepcopy(x))
            data = x.strip("\n").split(";")
            print(f"current data is {data}")
            knotList.append(data[0].strip(" "))
            DTList.append(data[1].strip(" "))
            pList.append(int(data[2].strip(" p = ")))

            qstrings = data[3].strip(" q = ").strip("[").strip("]").split(',')
            qvals = []
            for s in qstrings:
                if s.strip() != "":
                    qvals.append(int(s))
            qList.append(qvals)


    # Overwrite whatsLeft.txt with the cleaned list (no "Done!" lines).
    with WHATSLEFT.open("w") as outfile:
        outfile.writelines(whatsLeft)

    # Initialize / load progress.txt
    if not PROGRESS.exists():
        with PROGRESS.open("w") as outfile:
            outfile.write("Preparing to compare Turaev-Viro invariants of DBC's and surgeries for the given knots.")

    with PROGRESS.open("r") as f:
        progressLines = f.readlines()

    state1 = "[working on T-V invariant of DBC]"
    state2 = "[working on T-V invariant of surgery]"
    state0 = "[moving on to next knot]"

    state = 0

    if progressLines and (state1 in progressLines[-1]):
        state = 1

    if progressLines and (state2 in progressLines[-1]):
        state = 2
        # Drop the last line so we will overwrite it with fresh data.
        del progressLines[-1]

    with PROGRESS.open("w") as outfile:
        outfile.writelines(progressLines)

    newqList = copy.deepcopy(qList)

    # Main loop over remaining knots
    for k in range(len(knotList)):
        p = pList[k]

        # If there are no slopes left for this knot, just mark it Done.
        if not qList[k]:
            print(f"{knotList[k]} - no remaining slopes q; marking Done.")
            whatsLeft[k] = "Done!\n"
            with WHATSLEFT.open("w") as outfile:
                outfile.writelines(whatsLeft)
            continue

        fail = 0
        turaevViroCalculated = 0

        print(knotList[k])

        comment = "\n" + "Calculating Turaev-Viro invariants for K = " + str(knotList[k])

        # If we're starting fresh on this knot, record that in progress.txt.
        if state == 0:
            progressLines.append(comment + "\n")
            state = 1
            progressLines.append(state1)
            with PROGRESS.open("w") as outfile:
                outfile.writelines(progressLines)

        # Build manifold for the knot complement from the DT description
        K = snappy.Manifold(DTList[k])

        # --- Step 1: T-V invariant of DBC with time limit ---
        if turaevViroCalculated == 0:
            C = K.covers(2)[0]
            C.dehn_fill((1, 0), 0)
            C.simplify()
            Cfill = C.filled_triangulation()
            Cfill.simplify()
            isosigCover = Cfill.triangulation_isosig()

            CoverTri = regina.Triangulation3.fromIsoSig(isosigCover)
            CoverTri.intelligentSimplify()

            starttime = time.time()
            tvCover = CoverTri.turaevViro(5, alg=regina.ALG_TREEWIDTH)
            endtime = time.time()
            runtime = endtime - starttime

            turaevViroCalculated = 1
            print(tvCover)
            print(runtime)

            if runtime > maxtime:
                msg = "Too slow on cover; aborting this run early."
                print("Too slow! Restarting.")
                with PROGRESS.open("a") as outfile:
                    outfile.write("\n" + msg + "\n")
                # Abort this run; leave remaining slopes for this knot in whatsLeft.
                # Next run will rebuild state from whatsLeft.txt.
                return False

            comment = "T-V of DBC is " + str(tvCover)
            if state == 1:
                progressLines[-1] = comment + "\n"
                state = 2
                with PROGRESS.open("w") as outfile:
                    outfile.writelines(progressLines)

        # --- Step 2: T-V invariants for surgeries p/q ---
        for q in qList[k]:
            progressLines.append(state2)
            with PROGRESS.open("w") as outfile:
                outfile.writelines(progressLines)
            state = 2

            # Fresh copy of K for each surgery
            Y = K.copy()
            Y.dehn_fill((p, q), 0)
            Y.simplify()
            Yfill = Y.filled_triangulation()
            Yfill.simplify()
            isosigSurgery = Yfill.triangulation_isosig()

            SurgeryTri = regina.Triangulation3.fromIsoSig(isosigSurgery)
            SurgeryTri.intelligentSimplify()
            SurgeryTri.intelligentSimplify()
            SurgeryTri.intelligentSimplify()
            tvSurgery = SurgeryTri.turaevViro(5, alg=regina.ALG_TREEWIDTH)

            print(tvSurgery)

            comment = "T-V of surgery with q = " + str(q) + " is " + str(tvSurgery)
            if progressLines:
                progressLines[-1] = comment + "\n"
            else:
                progressLines.append(comment + "\n")

            with PROGRESS.open("w") as outfile:
                outfile.writelines(progressLines)

            # --- Step 3: compare cover vs surgery ---
            if tvSurgery == tvCover:
                # T-V invariants agree; this q goes to exceptions.
                if fail == 0:
                    fail_values = []
                    fail = 1
                temp = ("Failed to distinguish using Turaev-Viro invariants; for q = " +
                        str(q) + "; both Turaev-Viro invariants equal " + str(tvSurgery))
                with PROGRESS.open("a") as outfile:
                    outfile.write("\n")
                    outfile.write(temp)

                exceptions.append(
                    f"{knotList[k]}; {DTList[k]}; p = {p}; q = {q}\n"
                )
                with EXCEPTIONS.open("w") as outfile:
                    outfile.writelines(exceptions)

                fail_values.append(q)

            # In any case (success or failure), this q is now PROCESSED.
            newqList[k].remove(q)
            whatsLeft[k] = (str(knotList[k]) + "; " +
                            DTList[k] + "; p = " + str(p) +
                            "; q = " + str(newqList[k]) + "\n")
            with WHATSLEFT.open("w") as outfile:
                outfile.writelines(whatsLeft)

            if newqList[k] == []:
                whatsLeft[k] = "Done!\n"
                with WHATSLEFT.open("w") as outfile:
                    print(whatsLeft)
                    outfile.writelines(whatsLeft)

        if fail == 0:
            progressLines.append("Successfully distinguished remaining surgeries from DBC.\n")
            with PROGRESS.open("w") as outfile:
                print(progressLines)
                outfile.writelines(progressLines)

        state = 0

    # If we reach here, no maxtime cutoff occurred: all remaining knots processed.
    return True

if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description=(
            "Run the Turaev–Viro comparison stage on a dataset folder.\n\n"
            "This expects the folder to contain failList.txt (from the HF + Casson stage) "
            "and will read/update whatsLeft.txt, exceptions.txt, and progress.txt."
        )
    )
    parser.add_argument(
        "base",
        help="Path to the dataset folder (e.g. test_3-12 or retest_14)",
    )
    parser.add_argument(
        "--maxtime",
        type=float,
        default=500000000000.0,
        help="Maximum allowed time (in seconds) for computing TV of the cover (default: 1.4)",
    )

    args = parser.parse_args()
    base_path = Path(args.base).resolve()

    ok = run_tv_compare(base_path, maxtime=args.maxtime)
    if ok:
        print("Turaev–Viro stage completed.")
        sys.exit(0)
    else:
        print(
            "Turaev–Viro stage halted early due to a slow cover; "
            "re-run to continue processing remaining slopes."
        )
        sys.exit(1)
