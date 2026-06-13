"""STRAC Calculator — Streamlit UI。

計算ロジックは strac.py に分離してある。このモジュールは表示のみを担当する。
"""

from typing import Optional

import pandas as pd
import streamlit as st

from strac import (
    StracValues,
    compute_hstrac,
    compute_mq_strategy,
    compute_tstrac,
    solve_basic,
)

# ページ設定
st.set_page_config(
    page_title="STRAC Calculator",
    page_icon="🧮",
    layout="wide",
)

# 5 つの基本値のキー（セッションステートで使い回す）
VALUE_KEYS = ("p", "v", "q", "f", "g")


def initialize_session_state() -> None:
    """セッションステートを初期化する。"""
    if "current_values" not in st.session_state:
        st.session_state.current_values = {key: 0.0 for key in VALUE_KEYS}


def current_values() -> StracValues:
    """直近の Basic Calculation 結果を StracValues として取り出す。"""
    cv = st.session_state.current_values
    return StracValues(cv["p"], cv["v"], cv["q"], cv["f"], cv["g"])


def as_dict(sv: StracValues) -> dict:
    """StracValues を P/V/Q/F/G の入力初期値 dict に変換する。"""
    return {key: getattr(sv, key) for key in VALUE_KEYS}


def metric_ratio(
    label: str,
    value: Optional[float],
    suffix: str = "",
    fmt: str = "{:.1f}",
) -> None:
    """比率系メトリクスを表示する。value が None なら 'undefined'。"""
    if value is None:
        st.metric(label, "undefined")
    else:
        st.metric(label, fmt.format(value) + suffix)


def render_basic_results(
    sv: StracValues,
    title: str = "Results",
    show_ratios: bool = True,
) -> None:
    """Basic 計算結果を表示する共通関数。"""
    st.subheader(title)

    columns = st.columns(3 if show_ratios else 2)

    with columns[0]:
        st.write("**Primary Values**")
        st.metric("P", f"{sv.p:.1f}")
        st.metric("V", f"{sv.v:.1f}")
        st.metric("M", f"{sv.m:.1f}")
        st.metric("Q", f"{sv.q:.1f}")

    with columns[1]:
        st.write("**Products**")
        st.metric("PQ", f"{sv.pq:.1f}")
        st.metric("VQ", f"{sv.vq:.1f}")
        st.metric("MQ", f"{sv.mq:.1f}")
        st.metric("F", f"{sv.f:.1f}")
        st.metric("G", f"{sv.g:.1f}")

    if show_ratios:
        with columns[2]:
            st.write("**Ratios**")
            metric_ratio("V%", sv.v_percent, suffix="%")
            metric_ratio("FM", sv.fm_percent, suffix="%")
            metric_ratio("Q0", sv.q0)


def _value_inputs(key_prefix, label_fmt, defaults=None):
    """P/V/Q/F/G の number_input を 2 カラムに並べて値を返す。

    key_prefix: ウィジェット key の接頭辞。
    label_fmt:  記号("P" 等)から表示ラベルを作る関数。例 lambda s: f"{s}T =".
    defaults:   各記号の初期値 dict。None のとき初期値は空欄（Basic タブ用）。
    """
    if defaults is None:
        defaults = {key: None for key in VALUE_KEYS}
    steps = {"p": 1.0, "v": 1.0, "q": 1.0, "f": 10.0, "g": 10.0}

    def field(col, key):
        with col:
            return st.number_input(
                label_fmt(key.upper()),
                value=defaults[key],
                format="%.1f",
                step=steps[key],
                key=f"{key_prefix}_{key}",
            )

    col1, col2 = st.columns(2)
    return tuple(field(col1 if key in "pvq" else col2, key) for key in VALUE_KEYS)


def render_basic_tab() -> None:
    st.header("Basic Calculation")
    st.write("Enter values (leave blank to calculate automatically)")

    p, v, q, f, g = _value_inputs("basic", lambda s: f"{s} =")

    if st.button("Calculate Basic", type="primary"):
        try:
            sv = solve_basic(p, v, q, f, g)
        except ValueError as e:
            st.error(str(e))
            return
        st.session_state.current_values = {
            "p": sv.p, "v": sv.v, "q": sv.q, "f": sv.f, "g": sv.g,
        }
        render_basic_results(sv)


def render_tstrac_tab() -> None:
    st.header("T-STRAC (Target Analysis)")

    current = current_values()
    if all(getattr(current, key) == 0 for key in VALUE_KEYS):
        st.warning("Please run Basic Calculation first!")
        return

    st.write("Enter target values (leave blank to use current values)")
    pt, vt, qt, ft, gt = _value_inputs("t", lambda s: f"{s}T =", as_dict(current))

    if not st.button("Calculate T-STRAC", type="primary"):
        return

    target = StracValues(pt, vt, qt, ft, gt)
    result = compute_tstrac(current, target)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Target Values")
        for label, value in zip("PVQFG", [pt, vt, qt, ft, gt]):
            st.metric(f"{label}T", f"{value:.1f}")
    with col2:
        st.subheader("Differences")
        for key in "PVQFG":
            st.metric(f"D{key}", f"{result.delta[key]:.1f}")

    st.subheader("Percentage Changes")
    cols = st.columns(5)
    for col, key in zip(cols, "PVQFG"):
        with col:
            metric_ratio(f"D{key}%", result.delta_percent[key], suffix="%")


def render_hstrac_tab() -> None:
    st.header("H-STRAC (Historical Analysis)")

    current = current_values()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Base Values")
        p2, v2, q2, f2, g2 = _value_inputs("h_base", lambda s: f"{s}(base) =", as_dict(current))
    with col2:
        st.subheader("New Values")
        zeros = {key: 0.0 for key in VALUE_KEYS}
        p_new, v_new, q_new, f_new, g_new = _value_inputs("h_new", lambda s: f"{s}(new) =", zeros)

    if not st.button("Calculate H-STRAC", type="primary"):
        return

    base = StracValues(p2, v2, q2, f2, g2)
    new = StracValues(p_new, v_new, q_new, f_new, g_new)

    # 入力値の整合性チェック: MQ = F + G が成り立つか
    if not base.is_consistent or not new.is_consistent:
        st.warning(
            f"⚠️ 入力値に不整合があります (MQ ≠ F + G)。"
            f" Base: MQ={base.mq:.1f}, F+G={base.f + base.g:.1f}"
            f" / New: MQ={new.mq:.1f}, F+G={new.f + new.g:.1f}"
        )

    result = compute_hstrac(base, new)

    st.subheader("H-STRAC Results")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("PK", f"{result.pk:.1f}")
        st.metric("VK", f"{-result.vk:.1f}")  # 表示は符号反転（原典準拠）
        st.metric("MK", f"{result.mk:.1f}")
        st.metric("QK", f"{result.qk:.1f}")
    with col2:
        st.metric("PQK", f"{result.pqk:.1f}")
        st.metric("VQK", f"{-result.vqk:.1f}")  # 表示は符号反転（原典準拠）
        st.metric("MQK", f"{result.mqk:.1f}")
        st.metric("FK", f"{-result.fk:.1f}")  # 表示は符号反転（原典準拠）
        st.metric("GK", f"{result.gk:.1f}")

    st.markdown("---")

    # 比較期(New)の値で Basic Calculation を表示
    render_basic_results(new, "Basic Calculation Results (using New Values)", show_ratios=False)

    st.subheader("New Values Ratios")
    col1, col2 = st.columns(2)
    with col1:
        metric_ratio("V% (New)", new.v_percent, suffix="%")
    with col2:
        metric_ratio("FM (New)", new.fm_percent, suffix="%")


def render_mq_strategy_tab() -> None:
    st.header("MQ-Strategy")

    col1, col2 = st.columns(2)
    with col1:
        mq = st.number_input("MQ =", value=0.0, format="%.1f", step=10.0, key="mq_value")
        v_mq = st.number_input("V =", value=0.0, format="%.1f", step=1.0, key="mq_v")
        strategy = st.selectbox("Strategy", ["PP (P-based)", "QQ (Q-based)"])
    with col2:
        start_val = st.number_input("Start value", value=0.0, format="%.1f", key="mq_start")
        end_val = st.number_input("End value", value=10.0, format="%.1f", key="mq_end")
        step_val = st.number_input("Step", value=1.0, format="%.1f", key="mq_step")

    if not st.button("Calculate MQ-Strategy", type="primary"):
        return

    by_price = strategy.startswith("PP")
    try:
        rows = compute_mq_strategy(mq, v_mq, start_val, end_val, step_val, by_price)
    except ValueError as e:
        st.error(str(e))
        return

    if not rows:
        return

    df = pd.DataFrame(rows)
    st.subheader("MQ-Strategy Results")
    st.dataframe(df, use_container_width=True)

    st.subheader("Visualization")
    if by_price:
        st.line_chart(data=df.set_index("P")[["Q"]])
    else:
        st.line_chart(data=df.set_index("Q")[["P"]])


def main() -> None:
    st.title("🧮 STRAC Calculator")

    initialize_session_state()

    st.sidebar.header("Settings")
    name = st.sidebar.text_input("Name", value="User")
    if name:
        st.sidebar.write(f"**{name}**")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Basic Calculation", "🎯 T-STRAC", "📈 H-STRAC", "⚡ MQ-Strategy"]
    )
    with tab1:
        render_basic_tab()
    with tab2:
        render_tstrac_tab()
    with tab3:
        render_hstrac_tab()
    with tab4:
        render_mq_strategy_tab()


if __name__ == "__main__":
    main()
