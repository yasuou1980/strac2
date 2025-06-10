import streamlit as st
import math
import pandas as pd

# ページ設定
st.set_page_config(
    page_title="STRAC Calculator",
    page_icon="🧮",  
    layout="wide"
)

def initialize_session_state():
    """セッションステートを初期化"""
    if 'current_values' not in st.session_state:
        st.session_state.current_values = {'p': 0, 'v': 0, 'q': 0, 'f': 0, 'g': 0}

def basic_calculation(p, v, q, f, g):
    """基本計算ロジック"""
    PI = math.pi
    
    # None を PI で置き換える
    p = PI if p is None else p
    v = PI if v is None else v
    q = PI if q is None else q
    f = PI if f is None else f
    g = PI if g is None else g
    
    # 計算ロジック
    if p == PI:
        if q != 0:
            p = (v * q + f + g) / q
        else:
            p = 0
    
    if v == PI:
        if q != 0:
            v = (p * q - f - g) / q
        else:
            v = 0
    
    if q == PI:
        if (p - v) != 0:
            q = (f + g) / (p - v)
        else:
            q = 0
    
    if f == PI:
        f = p * q - v * q - g
    
    if g == PI:
        g = p * q - v * q - f
    
    m = p - v
    pq = p * q
    vq = v * q
    mq = m * q
    
    return p, v, q, f, g, m, pq, vq, mq

def main():
    st.title("🧮 STRAC Calculator")
    
    # セッションステート初期化
    initialize_session_state()
    
    # サイドバーで名前入力
    st.sidebar.header("Settings")
    name = st.sidebar.text_input("Name", value="User")
    if name:
        st.sidebar.write(f"** {name}")
    
    # メインタブ
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Basic Calculation", "🎯 T-STRAC", "📈 H-STRAC", "⚡ MQ-Strategy"])
    
    # Basic Calculation タブ
    with tab1:
        st.header("Basic Calculation")
        st.write("Enter values (leave blank to calculate automatically)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            p_input = st.number_input("P =", value=None, format="%.1f", key="basic_p")
            v_input = st.number_input("V =", value=None, format="%.1f", key="basic_v")
            q_input = st.number_input("Q =", value=None, format="%.1f", key="basic_q")
        
        with col2:
            f_input = st.number_input("F =", value=None, format="%.1f", key="basic_f")
            g_input = st.number_input("G =", value=None, format="%.1f", key="basic_g")
        
        if st.button("Calculate Basic", type="primary"):
            result = basic_calculation(p_input, v_input, q_input, f_input, g_input)
            p, v, q, f, g, m, pq, vq, mq = result
            
            # 結果を保存
            st.session_state.current_values = {'p': p, 'v': v, 'q': q, 'f': f, 'g': g}
            
            # 結果表示
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Primary Values")
                st.metric("P", f"{p:.1f}")
                st.metric("V", f"{v:.1f}")
                st.metric("M", f"{m:.1f}")
                st.metric("Q", f"{q:.1f}")
            
            with col2:
                st.subheader("Products") 
                st.metric("PQ", f"{pq:.1f}")
                st.metric("VQ", f"{vq:.1f}")
                st.metric("MQ", f"{mq:.1f}")
                st.metric("F", f"{f:.1f}")
                st.metric("G", f"{g:.1f}")
            
            with col3:
                st.subheader("Ratios")
                v_percent = v / p * 100 if p != 0 else "undefined"
                fm_percent = f / mq * 100 if mq != 0 else "undefined"
                q0 = f / m if m != 0 else "undefined"
                
                if isinstance(v_percent, float):
                    st.metric("V%", f"{v_percent:.1f}%")
                else:
                    st.metric("V%", v_percent)
                
                if isinstance(fm_percent, float):
                    st.metric("FM", f"{fm_percent:.1f}%")
                else:
                    st.metric("FM", fm_percent)
                
                if isinstance(q0, float):
                    st.metric("Q0", f"{q0:.1f}")
                else:
                    st.metric("Q0", q0)
    
    # T-STRAC タブ
    with tab2:
        st.header("T-STRAC (Target Analysis)")
        
        if all(v == 0 for v in st.session_state.current_values.values()):
            st.warning("Please run Basic Calculation first!")
        else:
            st.write("Enter target values (leave blank to use current values)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pt = st.number_input("PT =", value=st.session_state.current_values['p'], format="%.1f", key="t_pt")
                vt = st.number_input("VT =", value=st.session_state.current_values['v'], format="%.1f", key="t_vt")
                qt = st.number_input("QT =", value=st.session_state.current_values['q'], format="%.1f", key="t_qt")
            
            with col2:
                ft = st.number_input("FT =", value=st.session_state.current_values['f'], format="%.1f", key="t_ft")
                gt = st.number_input("GT =", value=st.session_state.current_values['g'], format="%.1f", key="t_gt")
            
            if st.button("Calculate T-STRAC", type="primary"):
                # 差分計算
                p, v, q, f, g = [st.session_state.current_values[k] for k in ['p', 'v', 'q', 'f', 'g']]
                dp = pt - p
                dv = vt - v
                dq = qt - q
                df = ft - f
                dg = gt - g
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Target Values")
                    st.metric("PT", f"{pt:.1f}")
                    st.metric("VT", f"{vt:.1f}")
                    st.metric("QT", f"{qt:.1f}")
                    st.metric("FT", f"{ft:.1f}")
                    st.metric("GT", f"{gt:.1f}")
                
                with col2:
                    st.subheader("Differences")
                    st.metric("DP", f"{dp:.1f}")
                    st.metric("DV", f"{dv:.1f}")
                    st.metric("DQ", f"{dq:.1f}")
                    st.metric("DF", f"{df:.1f}")
                    st.metric("DG", f"{dg:.1f}")
                
                st.subheader("Percentage Changes")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    dp_pct = dp / p * 100 if p != 0 else "undefined"
                    if isinstance(dp_pct, float):
                        st.metric("DP%", f"{dp_pct:.1f}%")
                    else:
                        st.metric("DP%", dp_pct)
                
                with col2:
                    dv_pct = dv / v * 100 if v != 0 else "undefined"
                    if isinstance(dv_pct, float):
                        st.metric("DV%", f"{dv_pct:.1f}%")
                    else:
                        st.metric("DV%", dv_pct)
                
                with col3:
                    dq_pct = dq / q * 100 if q != 0 else "undefined"
                    if isinstance(dq_pct, float):
                        st.metric("DQ%", f"{dq_pct:.1f}%")
                    else:
                        st.metric("DQ%", dq_pct)
                
                with col4:
                    df_pct = df / f * 100 if f != 0 else "undefined"
                    if isinstance(df_pct, float):
                        st.metric("DF%", f"{df_pct:.1f}%")
                    else:
                        st.metric("DF%", df_pct)
                
                with col5:
                    dg_pct = dg / g * 100 if g != 0 else "undefined"
                    if isinstance(dg_pct, float):
                        st.metric("DG%", f"{dg_pct:.1f}%")
                    else:
                        st.metric("DG%", dg_pct)
    
    # H-STRAC タブ
    with tab3:
        st.header("H-STRAC (Historical Analysis)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Base Values")
            p2 = st.number_input("P(base) =", value=0.0, format="%.1f", key="h_p2")
            v2 = st.number_input("V(base) =", value=0.0, format="%.1f", key="h_v2")
            q2 = st.number_input("Q(base) =", value=0.0, format="%.1f", key="h_q2")
            f2 = st.number_input("F(base) =", value=0.0, format="%.1f", key="h_f2")
            g2 = st.number_input("G(base) =", value=0.0, format="%.1f", key="h_g2")
        
        with col2:
            st.subheader("New Values")
            p_new = st.number_input("P(new) =", value=0.0, format="%.1f", key="h_p_new")
            v_new = st.number_input("V(new) =", value=0.0, format="%.1f", key="h_v_new")
            q_new = st.number_input("Q(new) =", value=0.0, format="%.1f", key="h_q_new")
            f_new = st.number_input("F(new) =", value=0.0, format="%.1f", key="h_f_new")
            g_new = st.number_input("G(new) =", value=0.0, format="%.1f", key="h_g_new")
        
        if st.button("Calculate H-STRAC", type="primary"):
            # 計算
            m2 = p2 - v2
            m_new = p_new - v_new
            pq2 = p2 * q2
            pq_new = p_new * q_new
            vq2 = v2 * q2
            vq_new = v_new * q_new
            mq2 = m2 * q2
            mq_new = m_new * q_new
            
            # 差分計算
            pk = (p_new - p2) * (q_new + q2) / 2
            vk = (v_new - v2) * (q_new + q2) / 2
            mk = (m_new - m2) * (q_new + q2) / 2
            qk = (q_new - q2) * (m_new + m2) / 2
            ak = pq_new - pq2
            bk = vq_new - vq2
            ck = mq_new - mq2
            fk = f_new - f2
            gk = ck - fk
            
            st.subheader("H-STRAC Results")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("PK", f"{pk:.1f}")
                st.metric("VK", f"{-vk:.1f}")  # 符号反転
                st.metric("MK", f"{mk:.1f}")
                st.metric("QK", f"{qk:.1f}")
            
            with col2:
                st.metric("PQK", f"{ak:.1f}")
                st.metric("VQK", f"{-bk:.1f}")  # 符号反転
                st.metric("MQK", f"{ck:.1f}")
                st.metric("FK", f"{-fk:.1f}")  # 符号反転
                st.metric("GK", f"{gk:.1f}")
    
    # MQ-Strategy タブ
    with tab4:
        st.header("MQ-Strategy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mq = st.number_input("MQ =", value=0.0, format="%.1f", key="mq_value")
            v_mq = st.number_input("V =", value=0.0, format="%.1f", key="mq_v")
            strategy = st.selectbox("Strategy", ["PP (P-based)", "QQ (Q-based)"])
        
        with col2:
            start_val = st.number_input("Start value", value=0.0, format="%.1f", key="mq_start")
            end_val = st.number_input("End value", value=10.0, format="%.1f", key="mq_end")
            step_val = st.number_input("Step", value=1.0, format="%.1f", key="mq_step")
        
        if st.button("Calculate MQ-Strategy", type="primary"):
            if step_val == 0:
                st.error("Step cannot be 0")
            else:
                results = []
                
                if "PP" in strategy:
                    # P-based strategy
                    p = start_val
                    while (step_val > 0 and p <= end_val) or (step_val < 0 and p >= end_val):
                        m = p - v_mq
                        q = mq / m if m != 0 else 0
                        q = round(q * 10) / 10
                        results.append({
                            'P': round(p, 1), 'V': round(v_mq, 1), 'M': round(m, 1), 'Q': round(q, 1),
                            'PQ': round(p * q, 1), 'VQ': round(v_mq * q, 1), 'MQ': round(m * q, 1)
                        })
                        p += step_val
                        
                        # 無限ループを防ぐ
                        if len(results) > 100:
                            break
                else:
                    # Q-based strategy
                    q = start_val
                    while (step_val > 0 and q <= end_val) or (step_val < 0 and q >= end_val):
                        m = mq / q if q != 0 else 0
                        m = round(m * 10) / 10
                        p = v_mq + m
                        results.append({
                            'P': round(p, 1), 'V': round(v_mq, 1), 'M': round(m, 1), 'Q': round(q, 1),
                            'PQ': round(p * q, 1), 'VQ': round(v_mq * q, 1), 'MQ': round(m * q, 1)
                        })
                        q += step_val
                        
                        # 無限ループを防ぐ
                        if len(results) > 100:
                            break
                
                if results:
                    df = pd.DataFrame(results)
                    st.subheader("MQ-Strategy Results")
                    st.dataframe(df, use_container_width=True)
                    
                    # チャート表示
                    st.subheader("Visualization")
                    if "PP" in strategy:
                        st.line_chart(data=df.set_index('P')[['Q']])
                    else:
                        st.line_chart(data=df.set_index('Q')[['P']])

if __name__ == "__main__":
    main()
