from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Tuple, List

def clamp(lo: float, hi: float, x: float) -> float:
    return max(lo, min(hi, x))

def normalize_to_1_10(x: float, x_min: float=0.0, x_max: float=10.0) -> float:
    # normalização linear para 1..10
    if x_max <= x_min:
        return 1.0
    t = (x - x_min) / (x_max - x_min)
    return clamp(1.0, 10.0, 1.0 + 9.0 * t)

def compute_complexity(T: int, D: int, K: int, A: int) -> float:
    C_raw = 0.4*T + 0.2*D + 0.2*K + 0.2*A
    # assume C_raw em faixa 0..20 típ., normaliza 1..10
    return normalize_to_1_10(C_raw, 0.0, 20.0)

def compute_uncertainty(ambiguous_items: int, total_steps: int) -> float:
    if total_steps <= 0:
        return 1.0
    return clamp(0.0, 1.0, ambiguous_items/total_steps)

def compute_lmax(C: float) -> int:
    return min(int(math.ceil(1.5*C)), 20)

def compute_sfc(SS_local: float, IEC: float, IRO_total: float) -> float:
    # versões congeladas
    IRO_n = clamp(0.0, 1.0, IRO_total/100.0)
    base = 0.7*clamp(0,100,SS_local) + 0.3*clamp(0,100,IEC)
    sfc = base * (1 - IRO_n)
    if IRO_total > 40:
        sfc *= 0.7
    return clamp(0.0, 100.0, sfc)

def compute_delta(prev: float, cur: float) -> float:
    if prev == 0:
        return 1.0
    return abs(cur-prev)/abs(prev)

def compute_iec(distinct_approaches: int, n_solutions: int) -> float:
    if n_solutions <= 0:
        return 0.0
    return clamp(0.0, 100.0, (distinct_approaches/n_solutions)*100.0)
