from core.metrics import compute_sfc, compute_lmax, compute_delta

def test_sfc_range():
    assert 0 <= compute_sfc(0,0,100) <= 100
    assert compute_sfc(100,100,0) == 100

def test_lmax_bounds():
    assert compute_lmax(1) == 2
    assert compute_lmax(10) == 15

def test_delta_zero_safe():
    assert compute_delta(0, 10) == 1.0
