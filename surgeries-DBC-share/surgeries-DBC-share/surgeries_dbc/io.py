# surgeries_dbc/io.py
#
# All filesystem I/O: read knot lists, write and read classical invariant lists,
# and write HF/Casson comparison logs.

from pathlib import Path
from typing import List

import sympy as sym

from .models import KnotRecord
from .hf_casson import DTconvertFull


# --------------------------------------------------------------------
# Base knot data
# --------------------------------------------------------------------

def load_knot_records(base: Path) -> List[KnotRecord]:
    """
    Load the basic knot data (names + DT codes) from:
      - knotList.txt
      - DTList.txt
      - numDTList.txt
    and return a list of KnotRecord objects.
    """
    names      = (base / "knotList.txt").read_text().splitlines()
    dt_alpha   = (base / "DTList.txt").read_text().splitlines()
    dt_numeric = (base / "numDTList.txt").read_text().splitlines()

    if not (len(names) == len(dt_alpha) == len(dt_numeric)):
        raise ValueError("Lengths of knotList, DTList, numDTList do not match.")

    records: List[KnotRecord] = []
    for name, da, dn in zip(names, dt_alpha, dt_numeric):
        records.append(
            KnotRecord(
                name=name.strip(),
                dt_alpha=da.strip(),
                dt_numeric=dn.strip()
            )
        )
    return records


# --------------------------------------------------------------------
# Classical invariants: write + read (full / heavy path)
# --------------------------------------------------------------------

def write_classical_lists(base: Path, records: List[KnotRecord]) -> None:
    """
    Write detList.txt, aList.txt, sigList.txt, jonesList.txt, cassonList.txt
    from the invariants stored in the KnotRecord objects.
    """
    det_lines    = []
    a_lines      = []
    sig_lines    = []
    jones_lines  = []
    casson_lines = []

    for rec in records:
        det_lines.append(str(rec.det))
        a_lines.append(str(rec.A))
        sig_lines.append(str(rec.signature))
        jones_lines.append(str(rec.jones_expr))
        casson_lines.append(str(rec.casson_dbc))

    (base / "detList.txt").write_text("\n".join(det_lines))
    (base / "aList.txt").write_text("\n".join(a_lines))
    (base / "sigList.txt").write_text("\n".join(sig_lines))
    (base / "jonesList.txt").write_text("\n".join(jones_lines))
    (base / "cassonList.txt").write_text("\n".join(casson_lines))


def load_classical_lists(base: Path, records: List[KnotRecord]) -> None:
    """
    Read detList.txt, aList.txt, sigList.txt, jonesList.txt, cassonList.txt
    and populate the corresponding fields on each KnotRecord.

    This is the original (heavy) loader: it parses Jones and Casson data
    as Sympy expressions. For reruns where we only need scalars, see
    load_classical_scalars_only().
    """
    det_lines    = (base / "detList.txt").read_text().splitlines()
    a_lines      = (base / "aList.txt").read_text().splitlines()
    sig_lines    = (base / "sigList.txt").read_text().splitlines()
    jones_lines  = (base / "jonesList.txt").read_text().splitlines()
    casson_lines = (base / "cassonList.txt").read_text().splitlines()

    n = len(records)
    if not (len(det_lines) == len(a_lines) == len(sig_lines) == len(jones_lines) == len(casson_lines) == n):
        raise ValueError("Classical invariant list lengths do not match number of records.")

    for rec, d_s, a_s, sig_s, j_s, cass_s in zip(
        records, det_lines, a_lines, sig_lines, jones_lines, casson_lines
    ):
        # Determinant and signature are integers
        rec.det = int(d_s.strip())
        rec.signature = int(sig_s.strip())

        # A(K), Jones, and Casson are Sympy-readable rationals/expressions
        rec.A = sym.sympify(a_s.strip())
        rec.jones_expr = sym.sympify(j_s.strip())
        rec.casson_dbc = sym.sympify(cass_s.strip())

def write_sig_jones_lists(base: Path, records: List[KnotRecord]) -> None:
    """
    Write signature and Jones polynomial lists in the simple text formats:
      - sigList.txt   : one integer per line (or blank if not computed)
      - jonesList.txt : one expression per line (or blank if not computed)

    This mirrors the original project's files, but we do NOT assume that
    every record has these invariants filled in; missing ones are written as
    empty lines.
    """
    sig_lines   = []
    jones_lines = []

    for rec in records:
        # Signature: integer or blank
        if rec.signature is None:
            sig_lines.append("")
        else:
            sig_lines.append(str(int(rec.signature)))

        # Jones: Sympy expression string or blank
        if rec.jones_expr is None:
            jones_lines.append("")
        else:
            jones_lines.append(str(rec.jones_expr))

    (base / "sigList.txt").write_text("\n".join(sig_lines))
    (base / "jonesList.txt").write_text("\n".join(jones_lines))


# --------------------------------------------------------------------
# Classical invariants: fast-path reload (scalars only)
# --------------------------------------------------------------------

def classical_outputs_exist(base: Path) -> bool:
    """
    Return True if all *scalar* classical invariant files exist in `base`.

    We intentionally only require the scalar data that later stages need:
      - detList.txt
      - aList.txt
      - sigList.txt
      - cassonList.txt

    Jones/Alexander polynomials are *not* required for reloads, to keep
    Stage 2 fast on reruns.
    """
    required = [
        "detList.txt",
        "aList.txt",
        "sigList.txt",
        "cassonList.txt",
    ]
    return all((base / name).is_file() for name in required)


def load_classical_scalars_only(base: Path, records: List[KnotRecord]) -> None:
    """
    Lightweight reload for Stage 2.

    This:
      - reads scalar invariants from text files in `base`,
      - populates only the fields needed by HF + Casson and Turaev–Viro:
          * determinant (rec.det)
          * A-value (rec.A)
          * signature (rec.signature)
          * Casson invariant of the double branched cover (rec.casson_dbc)

    It does *not*:
      - read or parse jonesList.txt,
      - parse large Sympy polynomials.

    This keeps Stage 2 reloads much faster on reruns.
    """
    det_lines    = (base / "detList.txt").read_text().splitlines()
    a_lines      = (base / "aList.txt").read_text().splitlines()
    sig_lines    = (base / "sigList.txt").read_text().splitlines()
    casson_lines = (base / "cassonList.txt").read_text().splitlines()

    n = len(records)
    if not (len(det_lines) == len(a_lines) == len(sig_lines) == len(casson_lines) == n):
        raise ValueError(
            "Scalar classical invariant list lengths do not match number of records."
        )

    for rec, d_s, a_s, sig_s, cass_s in zip(
        records, det_lines, a_lines, sig_lines, casson_lines
    ):
        rec.det = int(d_s.strip())
        rec.A = sym.sympify(a_s.strip())              # typically a small rational
        rec.signature = int(sig_s.strip())
        rec.casson_dbc = sym.sympify(cass_s.strip())  # usually a small rational


# --------------------------------------------------------------------
# HF/Casson output: results log + failList
# --------------------------------------------------------------------

def write_hf_outputs(
    base: Path,
    records: List[KnotRecord],
    output_log: list[str],
) -> None:
    """
    Write:
      - Casson-comparison-results.txt (full log)
      - failList.txt (lines for knots where Casson cannot distinguish)

    failList.txt lines are in the original format expected by TV-compare:
      name; DT:[...]; p = <p>; q = [q1, q2, ...]
    """
    # Full log
    (base / "Casson-comparison-results.txt").write_text(
        "\n".join(output_log)
    )

    fail_lines: list[str] = []
    for rec in records:
        if not rec.casson_fail_q:
            continue
        p = abs(int(rec.det))
        dt_full = DTconvertFull(rec.dt_alpha)
        line = f"{rec.name}; {dt_full}; p = {p}; q = {rec.casson_fail_q}"
        fail_lines.append(line.replace("\n", " "))

    (base / "failList.txt").write_text("\n".join(fail_lines))
