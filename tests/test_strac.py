"""strac.py の計算ロジックのテスト。

期待値は原典「STRAC-T/M/1」の付録に掲載された実行例に基づく。
pytest でも、直接 `python tests/test_strac.py` でも実行できる。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strac import (  # noqa: E402
    StracValues,
    compute_hstrac,
    compute_mq_strategy,
    compute_tstrac,
    solve_basic,
)


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def test_basic_example_all_filled():
    # 原典 STRAC-1 例: P=30, V=20, Q=10, F=80, G=20
    sv = solve_basic(30, 20, 10, 80, 20)
    assert approx(sv.m, 10)
    assert approx(sv.pq, 300)
    assert approx(sv.vq, 200)
    assert approx(sv.mq, 100)
    assert approx(sv.v_percent, 66.6666667)
    assert approx(sv.fm_percent, 80)
    assert approx(sv.q0, 8)
    assert sv.is_consistent


def test_solve_for_each_blank():
    assert approx(solve_basic(None, 20, 10, 80, 20).p, 30)
    assert approx(solve_basic(30, None, 10, 80, 20).v, 20)
    assert approx(solve_basic(30, 20, None, 80, 20).q, 10)
    assert approx(solve_basic(30, 20, 10, None, 20).f, 80)
    assert approx(solve_basic(30, 20, 10, 80, None).g, 20)


def test_two_blanks_raises():
    try:
        solve_basic(None, None, 10, 80, 20)
    except ValueError as e:
        assert "P" in str(e) and "V" in str(e)
    else:
        raise AssertionError("空欄2つで ValueError を期待")


def test_divide_by_zero_guards():
    # Q=0 で P を逆算 → 0 にフォールバック
    assert approx(solve_basic(None, 20, 0, 80, 20).p, 0)
    # P=V で Q を逆算 → 0 にフォールバック
    assert approx(solve_basic(20, 20, None, 80, 20).q, 0)


def test_undefined_ratios():
    sv = StracValues(0, 0, 0, 0, 0)
    assert sv.v_percent is None
    assert sv.fm_percent is None
    assert sv.q0 is None


def test_tstrac_differences():
    current = StracValues(30, 20, 10, 80, 20)
    target = StracValues(28, 22, 8, 100, 0)
    r = compute_tstrac(current, target)
    assert approx(r.delta["P"], -2)
    assert approx(r.delta["V"], 2)
    assert approx(r.delta["Q"], -2)
    assert approx(r.delta["F"], 20)
    assert approx(r.delta["G"], -20)
    assert approx(r.delta_percent["P"], -6.6666667)
    assert approx(r.delta_percent["F"], 25)
    # G(current)=20 → DG% = -20/20*100 = -100
    assert approx(r.delta_percent["G"], -100)


def test_tstrac_percent_undefined_when_zero():
    current = StracValues(30, 20, 10, 80, 0)  # G=0
    r = compute_tstrac(current, StracValues(30, 20, 10, 80, 5))
    assert r.delta_percent["G"] is None


def test_hstrac_example():
    # 原典 H-STRAC 例
    base = StracValues(30, 20, 10, 80, 20)
    new = StracValues(29, 19, 11, 100, 10)
    r = compute_hstrac(base, new)
    assert approx(r.pk, -10.5)
    assert approx(r.vk, -10.5)   # 表示は反転して 10.5
    assert approx(r.mk, 0)
    assert approx(r.qk, 10)
    assert approx(r.pqk, 19)
    assert approx(r.vqk, 9)      # 表示は反転して -9
    assert approx(r.mqk, 10)
    assert approx(r.fk, 20)      # 表示は反転して -20
    assert approx(r.gk, -10)     # GK = MQK - FK = 10 - 20


def test_mq_strategy_price_based():
    # MQ=360, V=14, P:20→24 step1（原典 P-戦略 例）
    rows = compute_mq_strategy(360, 14, 20, 24, 1, by_price=True)
    assert len(rows) == 5
    assert rows[0]["P"] == 20 and rows[0]["Q"] == 60
    assert rows[2]["P"] == 22 and rows[2]["Q"] == 45
    assert rows[4]["P"] == 24 and rows[4]["Q"] == 36


def test_mq_strategy_quantity_based():
    rows = compute_mq_strategy(360, 14, 20, 50, 5, by_price=False)
    assert rows[0]["Q"] == 20
    assert approx(rows[0]["M"], 18)  # 360/20
    assert approx(rows[0]["P"], 32)  # V + M


def test_mq_strategy_zero_step_raises():
    try:
        compute_mq_strategy(360, 14, 20, 24, 0, by_price=True)
    except ValueError:
        pass
    else:
        raise AssertionError("step=0 で ValueError を期待")


def test_mq_strategy_row_cap():
    rows = compute_mq_strategy(100, 1, 0, 1000, 0.001, by_price=True)
    assert len(rows) == 101


if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in funcs:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(funcs)} passed")
