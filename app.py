"""
DFM Scenario Analysis Tool v3.2
Dubai Financial Market - Earnings Sensitivity Analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(page_title="DFM Scenario Analysis", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    .stApp { background-color: #FFFFFF; }
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    h1, h2, h3, p, span, div, label { font-family: 'Inter', sans-serif !important; color: #1A1A1A; }
    h1, h2, h3 { font-weight: 600 !important; }
    .main-header { color: #0066CC; font-size: 2rem; font-weight: 700; }
    .sub-header { color: #666666; font-size: 0.95rem; }
    .metric-card-highlight { background: #E6F0FA; border: 1px solid #0066CC; border-radius: 8px; padding: 1.25rem; margin: 0.5rem 0; }
    .metric-label { color: #666666; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500; }
    .metric-value-blue { color: #0066CC; font-size: 1.5rem; font-weight: 600; font-family: 'JetBrains Mono', monospace !important; }
    [data-testid="stSidebar"] { background-color: #F5F5F5; }
    [data-testid="stSidebar"] .stMarkdown h3 { color: #0066CC !important; font-size: 0.85rem; text-transform: uppercase; border-bottom: 2px solid #0066CC; padding-bottom: 0.5rem; margin-top: 1.5rem; }
    .section-divider { border: none; height: 1px; background: #E0E0E0; margin: 1.5rem 0; }
    .info-box { background: #E6F0FA; border-left: 4px solid #0066CC; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    .success-box { background: #E8F5E9; border-left: 4px solid #28A745; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    .warning-box { background: #FFF3E0; border-left: 4px solid #FF9800; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stMetricValue"] { color: #0066CC !important; }
</style>
""", unsafe_allow_html=True)

# Default Q3 2025 values (AED thousands)
DEFAULT = {
    'trading_commission': 310_195,
    'investment_income': 165_348,
    'investment_deposits': 4_134_622,
    'investments_amortised_cost': 367_717,
    'total_traded_value': 165_000_000,
    'period_months': 9,
    'trading_days': 252,
    'commission_rate_bps': 25.0
}

def parse_pdf(file):
    try:
        import pdfplumber
    except ImportError:
        return None
    data = {'trading_commission': None, 'investment_income': None, 'investment_deposits': None, 
            'investments_amortised_cost': None, 'period_months': 9, 'items': []}
    try:
        with pdfplumber.open(file) as pdf:
            text = "".join([p.extract_text() or "" for p in pdf.pages])
            # Trading commission - look for 9-month figure (3rd number in pattern)
            m = re.search(r'Trading commission fees\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)', text, re.I)
            if m:
                data['trading_commission'] = float(m.group(3).replace(',', ''))
                data['items'].append(f"Trading Comm: AED {data['trading_commission']:,.0f}K")
            # Investment income
            m = re.search(r'Investment income\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)', text, re.I)
            if m:
                data['investment_income'] = float(m.group(3).replace(',', ''))
                data['items'].append(f"Inv Income: AED {data['investment_income']:,.0f}K")
            # Investment deposits
            m = re.search(r'Investment deposits\s+\d+\s+([\d,]+)', text, re.I)
            if m:
                data['investment_deposits'] = float(m.group(1).replace(',', ''))
                data['items'].append(f"Deposits: AED {data['investment_deposits']:,.0f}K")
            # Sukuks
            m = re.search(r'Investments at amortised cost\s+\d+\s+([\d,]+)', text, re.I)
            if m:
                data['investments_amortised_cost'] = float(m.group(1).replace(',', ''))
                data['items'].append(f"Sukuks: AED {data['investments_amortised_cost']:,.0f}K")
            # Period
            if 'nine-month' in text.lower(): data['period_months'] = 9
            elif 'six-month' in text.lower(): data['period_months'] = 6
            elif 'year ended' in text.lower(): data['period_months'] = 12
    except Exception as e:
        st.error(f"PDF Error: {e}")
    return data if data['items'] else None

def parse_excel(file):
    data = {'total_traded_value': None, 'items': []}
    try:
        df = pd.read_excel(file, sheet_name=0, header=1)
        tv_col = next((c for c in df.columns if 'trade value' in str(c).lower()), None)
        if not tv_col: return None
        df['TV'] = pd.to_numeric(df[tv_col].astype(str).str.replace(',', ''), errors='coerce')
        name_col = next((c for c in df.columns if any(x in str(c).lower() for x in ['symbol', 'security'])), df.columns[0])
        for pat in ['Market Grand Total', 'Market Trades Total', 'Shares Grand Total']:
            mask = df[name_col].astype(str).str.contains(pat, case=False, na=False)
            if mask.any():
                val = df[mask].iloc[0]['TV']
                if pd.notna(val) and val > 0:
                    data['total_traded_value'] = float(val)
                    data['items'].append(f"Traded Value: AED {val:,.0f}")
                    break
    except Exception as e:
        st.error(f"Excel Error: {e}")
    return data if data['items'] else None

def fmt_m(v): return f"AED {v/1000:,.1f}M" if v and v > 0 else "N/A"
def fmt_b(v): return f"AED {v/1000000:,.1f}B" if v and v > 0 else "N/A"
def calc_comm(tv, bps): return tv * bps / 10000 if tv and bps and tv > 0 and bps > 0 else 0
def calc_inv(port, rate): return port * rate / 100 if port and rate is not None and port > 0 and rate >= 0 else 0

def main():
    st.markdown('<p class="main-header">📊 DFM Scenario Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Dubai Financial Market | Earnings Sensitivity Tool</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📁 Data Sources")
        st.markdown("### Financial Statement")
        fs_file = st.file_uploader("Upload PDF", type=['pdf'], key="fs")
        st.markdown("### Market Bulletin")  
        bul_file = st.file_uploader("Upload Excel", type=['xlsx', 'xls'], key="bul")
        st.markdown("---")
        st.markdown("### ⚙️ Manual Override")
        use_manual = st.checkbox("Enable manual entry", value=False)
    
    # Parse files
    fs = parse_pdf(fs_file) if fs_file else None
    bul = parse_excel(bul_file) if bul_file else None
    
    # Build data dict with defaults
    d = DEFAULT.copy()
    if fs:
        if fs.get('trading_commission'): d['trading_commission'] = fs['trading_commission']
        if fs.get('investment_income'): d['investment_income'] = fs['investment_income']
        if fs.get('investment_deposits'): d['investment_deposits'] = fs['investment_deposits']
        if fs.get('investments_amortised_cost'): d['investments_amortised_cost'] = fs['investments_amortised_cost']
        d['period_months'] = fs.get('period_months', 9)
    if bul and bul.get('total_traded_value'):
        d['total_traded_value'] = bul['total_traded_value']
    
    # Calculate derived
    d['portfolio'] = d['investment_deposits'] + d['investments_amortised_cost']
    d['adtv'] = d['total_traded_value'] / d['trading_days']
    d['comm_annual'] = d['trading_commission'] * 12 / d['period_months']
    d['inv_annual'] = d['investment_income'] * 12 / d['period_months']
    d['commission_rate_bps'] = (d['comm_annual'] / d['total_traded_value'] * 10000) if d['total_traded_value'] > 0 else 25.0
    
    # Manual overrides
    if use_manual:
        with st.sidebar:
            d['trading_commission'] = st.number_input("Trading Comm (AED K)", value=float(d['trading_commission']), min_value=0.0, step=1000.0)
            d['investment_income'] = st.number_input("Inv Income (AED K)", value=float(d['investment_income']), min_value=0.0, step=1000.0)
            d['portfolio'] = st.number_input("Portfolio (AED K)", value=float(d['portfolio']), min_value=0.0, step=10000.0)
            d['total_traded_value'] = st.number_input("Traded Value (AED K)", value=float(d['total_traded_value']), min_value=0.0, step=1000000.0)
            d['commission_rate_bps'] = st.number_input("Comm Rate (bps)", value=float(d['commission_rate_bps']), min_value=0.1, max_value=100.0, step=0.5)
            d['adtv'] = d['total_traded_value'] / d['trading_days']
            d['comm_annual'] = d['trading_commission'] * 12 / d['period_months']
            d['inv_annual'] = d['investment_income'] * 12 / d['period_months']
    
    # Status
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if fs:
            st.markdown(f'<div class="success-box"><strong>✅ Financial Statement</strong><br>{"<br>".join(fs["items"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box"><strong>⚠️ No FS</strong> - Using Q3 2025 defaults</div>', unsafe_allow_html=True)
    with c2:
        if bul:
            st.markdown(f'<div class="success-box"><strong>✅ Bulletin</strong><br>{"<br>".join(bul["items"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box"><strong>⚠️ No Bulletin</strong> - Using 2025 defaults</div>', unsafe_allow_html=True)
    
    # Metrics
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📋 Baseline Metrics")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card-highlight"><div class="metric-label">Trading Commission ({d["period_months"]}M)</div><div class="metric-value-blue">{fmt_m(d["trading_commission"])}</div><div style="color:#666;font-size:0.75rem">Annual: {fmt_m(d["comm_annual"])}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card-highlight"><div class="metric-label">Avg Daily Traded Value</div><div class="metric-value-blue">{fmt_m(d["adtv"])}</div><div style="color:#666;font-size:0.75rem">Total: {fmt_b(d["total_traded_value"])}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card-highlight"><div class="metric-label">Investment Portfolio</div><div class="metric-value-blue">{fmt_b(d["portfolio"])}</div><div style="color:#666;font-size:0.75rem">Deposits + Sukuks</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card-highlight"><div class="metric-label">Investment Income ({d["period_months"]}M)</div><div class="metric-value-blue">{fmt_m(d["investment_income"])}</div><div style="color:#666;font-size:0.75rem">Annual: {fmt_m(d["inv_annual"])}</div></div>', unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📉 Commission Fee", "📊 Traded Value", "💰 Interest Rate", "🔄 Combined"])
    
    # TAB 1: Commission Fee
    with tab1:
        st.markdown("### Commission Fee Scenario")
        ci, cr = st.columns([1, 2])
        with ci:
            # Use slider for traded value to avoid input validation issues
            tv_b = d['total_traded_value'] / 1e6  # Convert to billions
            tv1 = st.slider("Traded Value (AED Billions)", 10.0, 500.0, min(500.0, max(10.0, tv_b)), 5.0, key="t1tv") * 1e6
            cur_rate = st.slider("Current Commission Rate (bps)", 1.0, 50.0, min(50.0, max(1.0, d['commission_rate_bps'])), 0.5, key="t1cr")
            new_rate = st.slider("New Commission Rate (bps)", 1.0, 50.0, 20.0, 0.5, key="t1nr")
        with cr:
            cur_c, new_c = calc_comm(tv1, cur_rate), calc_comm(tv1, new_rate)
            chg = new_c - cur_c
            pct = (chg/cur_c*100) if cur_c > 0 else 0
            m1, m2, m3 = st.columns(3)
            m1.metric("Current", fmt_m(cur_c))
            m2.metric("Scenario", fmt_m(new_c), f"{new_rate-cur_rate:+.1f} bps")
            m3.metric("Impact", fmt_m(chg), f"{pct:+.1f}%", delta_color="normal" if chg >= 0 else "inverse")
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Current', x=['Commission'], y=[cur_c/1000], marker_color='#0066CC', text=[f'{cur_c/1000:,.0f}M'], textposition='outside'))
            fig.add_trace(go.Bar(name='Scenario', x=['Commission'], y=[new_c/1000], marker_color='#66B2FF', text=[f'{new_c/1000:,.0f}M'], textposition='outside'))
            fig.update_layout(barmode='group', height=300, plot_bgcolor='white', yaxis_title='AED M')
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 2: Traded Value
    with tab2:
        st.markdown("### Traded Value Scenario")
        ci, cr = st.columns([1, 2])
        with ci:
            method = st.radio("Input Method", ["ADTV × 252 days", "Total Annual Value"], key="t2m")
            if method == "ADTV × 252 days":
                adtv_m = d['adtv'] / 1000  # millions
                cur_adtv = st.slider("Current ADTV (AED M)", 100.0, 2000.0, min(2000.0, max(100.0, adtv_m)), 10.0, key="t2ca")
                new_adtv = st.slider("New ADTV (AED M)", 100.0, 2000.0, min(2000.0, max(100.0, adtv_m * 0.75)), 10.0, key="t2na")
                cur_ann, new_ann = cur_adtv * 1000 * 252, new_adtv * 1000 * 252
            else:
                tv_b = d['total_traded_value'] / 1e6
                cur_ann = st.slider("Current (AED B)", 50.0, 500.0, min(500.0, max(50.0, tv_b)), 5.0, key="t2cb") * 1e6
                new_ann = st.slider("New (AED B)", 50.0, 500.0, min(500.0, max(50.0, tv_b * 0.75)), 5.0, key="t2nb") * 1e6
            rate2 = st.slider("Commission Rate (bps)", 1.0, 50.0, min(50.0, max(1.0, d['commission_rate_bps'])), 0.5, key="t2r")
        with cr:
            cur_c2, new_c2 = calc_comm(cur_ann, rate2), calc_comm(new_ann, rate2)
            chg2 = new_c2 - cur_c2
            tv_pct = ((new_ann - cur_ann) / cur_ann * 100) if cur_ann > 0 else 0
            c_pct = (chg2 / cur_c2 * 100) if cur_c2 > 0 else 0
            m1, m2, m3 = st.columns(3)
            m1.metric("Current TV", fmt_b(cur_ann))
            m2.metric("New TV", fmt_b(new_ann), f"{tv_pct:+.1f}%")
            m3.metric("Commission Δ", fmt_m(chg2), f"{c_pct:+.1f}%", delta_color="normal" if chg2 >= 0 else "inverse")
            st.dataframe(pd.DataFrame({
                'Metric': ['Traded Value', 'ADTV', 'Commission'],
                'Current': [fmt_b(cur_ann), fmt_m(cur_ann/252), fmt_m(cur_c2)],
                'Scenario': [fmt_b(new_ann), fmt_m(new_ann/252), fmt_m(new_c2)],
                'Change': [f"{tv_pct:+.1f}%", f"{tv_pct:+.1f}%", f"{fmt_m(chg2)}"]
            }), hide_index=True)
    
    # TAB 3: Interest Rate
    with tab3:
        st.markdown("### Interest Rate Scenario")
        ci, cr = st.columns([1, 2])
        with ci:
            port_b = d['portfolio'] / 1e6
            port = st.slider("Portfolio (AED B)", 1.0, 10.0, min(10.0, max(1.0, port_b)), 0.1, key="t3p") * 1e6
            cur_ir = st.slider("Current Interest Rate (%)", 0.0, 10.0, 5.0, 0.25, key="t3cr")
            ir_chg = st.selectbox("Rate Change", ["+50 bps", "+25 bps", "No change", "-25 bps", "-50 bps", "-100 bps", "-150 bps"], index=4)
            chg_map = {"+50 bps": 50, "+25 bps": 25, "No change": 0, "-25 bps": -25, "-50 bps": -50, "-100 bps": -100, "-150 bps": -150}
            new_ir = max(0, cur_ir + chg_map[ir_chg] / 100)
            st.info(f"New Rate: **{new_ir:.2f}%**")
        with cr:
            cur_inv, new_inv = calc_inv(port, cur_ir), calc_inv(port, new_ir)
            inv_chg = new_inv - cur_inv
            inv_pct = (inv_chg / cur_inv * 100) if cur_inv > 0 else 0
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Income", fmt_m(cur_inv), f"@ {cur_ir:.2f}%")
            m2.metric("New Income", fmt_m(new_inv), f"@ {new_ir:.2f}%")
            m3.metric("Impact", fmt_m(inv_chg), f"{inv_pct:+.1f}%", delta_color="normal" if inv_chg >= 0 else "inverse")
            st.markdown(f'<div class="info-box"><strong>Calculation:</strong><br>Portfolio {fmt_b(port)} × {chg_map[ir_chg]:+d} bps = <strong>{fmt_m(inv_chg)}</strong></div>', unsafe_allow_html=True)
            sens = [{'Rate Δ': f"{r:+d} bps", 'New Rate': f"{max(0, cur_ir + r/100):.2f}%", 
                    'Income': fmt_m(calc_inv(port, max(0, cur_ir + r/100))), 
                    'Impact': fmt_m(calc_inv(port, max(0, cur_ir + r/100)) - cur_inv)} 
                   for r in [100, 50, 25, 0, -25, -50, -100, -150, -200]]
            st.dataframe(pd.DataFrame(sens), hide_index=True)
    
    # TAB 4: Combined
    with tab4:
        st.markdown("### Combined Scenario")
        cl, cr = st.columns(2)
        with cl:
            st.markdown("#### Inputs")
            tv_b = d['total_traded_value'] / 1e6
            ctv = st.slider("Traded Value (AED B)", 50.0, 500.0, min(500.0, max(50.0, tv_b)), 5.0, key="t4tv") * 1e6
            ccr = st.slider("Commission Rate (bps)", 1.0, 50.0, min(50.0, max(1.0, d['commission_rate_bps'])), 0.5, key="t4cr")
            port_b = d['portfolio'] / 1e6
            cport = st.slider("Portfolio (AED B)", 1.0, 10.0, min(10.0, max(1.0, port_b)), 0.1, key="t4p") * 1e6
            cir = st.slider("Interest Rate (%)", 0.0, 10.0, 5.0, 0.25, key="t4ir")
        with cr:
            st.markdown("#### Results")
            sc_comm = calc_comm(ctv, ccr)
            sc_inv = calc_inv(cport, cir)
            sc_tot = sc_comm + sc_inv
            bl_comm, bl_inv = d['comm_annual'], d['inv_annual']
            bl_tot = bl_comm + bl_inv
            st.dataframe(pd.DataFrame({
                'Stream': ['Trading Commission', 'Investment Income', 'TOTAL'],
                'Baseline': [fmt_m(bl_comm), fmt_m(bl_inv), fmt_m(bl_tot)],
                'Scenario': [fmt_m(sc_comm), fmt_m(sc_inv), fmt_m(sc_tot)],
                'Change': [fmt_m(sc_comm - bl_comm), fmt_m(sc_inv - bl_inv), fmt_m(sc_tot - bl_tot)]
            }), hide_index=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Commission", fmt_m(sc_comm), f"{(sc_comm - bl_comm)/1000:+,.0f}M")
            m2.metric("Investment", fmt_m(sc_inv), f"{(sc_inv - bl_inv)/1000:+,.0f}M")
            m3.metric("Total Δ", fmt_m(sc_tot - bl_tot), f"{(sc_tot - bl_tot)/bl_tot*100:+.1f}%" if bl_tot > 0 else "")
            fig4 = go.Figure(go.Waterfall(
                orientation="v", measure=["absolute", "relative", "relative", "total"],
                x=["Baseline", "Comm Δ", "Inv Δ", "Scenario"],
                y=[bl_tot/1000, (sc_comm - bl_comm)/1000, (sc_inv - bl_inv)/1000, sc_tot/1000],
                text=[f"{bl_tot/1000:,.0f}M", f"{(sc_comm - bl_comm)/1000:+,.0f}M", f"{(sc_inv - bl_inv)/1000:+,.0f}M", f"{sc_tot/1000:,.0f}M"],
                textposition="outside", connector={"line": {"color": "#0066CC"}},
                decreasing={"marker": {"color": "#DC3545"}}, increasing={"marker": {"color": "#28A745"}}, totals={"marker": {"color": "#0066CC"}}
            ))
            fig4.update_layout(title="Revenue Bridge", height=350, plot_bgcolor='white', yaxis_title="AED M", showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.caption("**Data:** Upload files or uses Q3 2025 defaults | **Disclaimer:** Internal analysis only")

if __name__ == "__main__":
    main()
