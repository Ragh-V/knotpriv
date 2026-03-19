# surgeries_dbc/invariants.py
#
# Compute classical invariants (Alexander, det, A, signature, Jones,
# Casson of the double branched cover) and store them in KnotRecord objects.

from pathlib import Path
from typing import List

import snappy
import regina
import sympy as sym
from sympy import sqrt, symbols

from .models import KnotRecord

# Sympy symbols used in polynomial expressions
x, y = symbols("x y")

def clean(input):
    """
    Normalize expressions from SnapPy/Regina into something Sympy can parse.
    """
    return sym.parse_expr(
        str(input)
        .replace('^', '**')
        .replace('+ ', '+')
        .replace('- ', '-')
        .replace(' x', '*x')
        .replace(' y', '*y')
    )

def snappyDT(dt_line: str) -> str:
    """
    Format a numeric DT code line for SnapPy's Link constructor.
    """
    return "DT: [(" + dt_line + ")]"

def alex_from_link(K) -> sym.Expr:
    """
    Compute Δ_K(x) via HOMFLY-PT, using the original recipe.
    """
    homfly = K.homflyAZ()
    expr = clean(homfly).subs(x, 1)
    expr = str(expr).replace('y', 'x')
    return sym.parse_expr(expr).subs(x, sqrt(x) - 1/sqrt(x))

def Avalue(alex_poly: sym.Expr) -> sym.Expr:
    """
    A(K) = (1/2) * Δ''_K(1).
    """
    dalex  = sym.diff(alex_poly, x)
    ddalex = sym.diff(dalex, x)
    return sym.Rational(1, 2) * ddalex.subs(x, 1)

def det_from_alex(alex_poly: sym.Expr) -> sym.Expr:
    """
    det(K) = Δ_K(-1).
    """
    return alex_poly.subs(x, -1)

def compute_classical_invariants(records: List[KnotRecord]) -> None:
    """
    Fill in det, A, signature, jones_expr, casson_dbc fields on each record.
    """
    num_knots = len(records)

    print("Computing Alexander polynomials, det(K), and A(K).")
    for k, rec in enumerate(records):
        # Regina link from alphabetical DT code
        K_regina = regina.Link.fromDT(rec.dt_alpha)

        alex_poly = alex_from_link(K_regina)
        detK = det_from_alex(alex_poly)
        A_val = Avalue(alex_poly)

        rec.det = int(detK)
        rec.A   = A_val

        if k % 500 == 0:
            print(f"{k} ({k/num_knots})")

    print("Computing signatures and Jones polynomials.")
    for k, rec in enumerate(records):
        # SnapPy link from numeric DT code
        K_snappy = snappy.Link(snappyDT(rec.dt_numeric))

        sig = K_snappy.signature()
        j_expr = clean(str(K_snappy.jones_polynomial()).replace('q', 'sqrt(x)'))

        rec.signature = int(sig)
        rec.jones_expr = j_expr

        if k % 500 == 0:
            print(f"{k} ({k/num_knots})")

    print("Computing Casson invariants of the double branched covers.")
    for k, rec in enumerate(records):
        # J'_K(-1)
        deriv_val = sym.diff(rec.jones_expr).subs(x, -1)

        sig   = sym.Rational(rec.signature)
        deriv = sym.Rational(deriv_val)
        detK  = sym.Rational(rec.det)

        casson = (sig/8) - ((deriv/detK)/12)
        rec.casson_dbc = casson

        if k % 500 == 0:
            print(f"{k} ({k/num_knots})")
