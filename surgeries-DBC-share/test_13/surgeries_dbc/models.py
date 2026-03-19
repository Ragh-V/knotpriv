# surgeries_dbc/models.py

from dataclasses import dataclass, field
from typing import Optional, List
from sympy import Expr

@dataclass
class KnotRecord:
    """
    A single knot in the dataset, together with all invariants and
    obstruction data we care about.
    """
    name: str
    dt_alpha: str        # alphabetical DT code (DTList.txt)
    dt_numeric: str      # numeric DT code (numDTList.txt)

    # Classical invariants
    det: Optional[int] = None           # determinant
    A: Optional[Expr] = None            # A(K) = 1/2*Δ''(1)
    signature: Optional[int] = None     # σ(K)
    jones_expr: Optional[Expr] = None   # J_K in Sympy format
    casson_dbc: Optional[Expr] = None   # Casson(Σ_2(K))

    # Surgery parameters / HF bounds
    m: Optional[int] = None
    n: Optional[int] = None
    HFbound: Optional[int] = None

    # HF obstruction + Casson comparison
    hf_min_rank: Optional[int] = None
    hf_obstruction_success: Optional[bool] = None
    casson_fail_q: List[int] = field(default_factory=list)
