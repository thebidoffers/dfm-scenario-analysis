"""
DFM Scenario Analysis Tool
Dubai Financial Market - Earnings Sensitivity Analysis
Dynamic file upload version

Author: DFM Finance Team
Version: 3.1.0
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(page_title="DFM Scenario Analysis", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    :root { --dfm-blue: #0066CC; --dfm-blue-light: #E6F0FA; --dfm-black: #1A1A1A; --dfm-gray: #666666; --dfm-gray-light: #F5F5F5; --dfm-green: #28A745; --dfm-red: #DC3545; }
    .stApp { background-color: #FFFFFF; }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; color: #1A1A1A !important; font-weight: 600 !important; }
    p, span, div, label { font-family: 'Inter', sans-serif !important; color: #1A1A1A; }
    .main-header { color: #0066CC; font-size: 2rem; font-weight: 700; margin-bottom: 0; }
    .sub-header { color: #666666; font-size: 0.95rem; margin-top: 0.25rem; }
    .metric-card-highlight { background: #E6F0FA; border: 1px solid #0066CC; border-radius: 8px; padding: 1.25rem; margin: 0.5rem 0; }
    .metric-label { color: #666666; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; font-weight: 500; }
    .metric-value-blue { color: #0066CC; font-size: 1.5rem; font-weight: 600; font-family: 'JetBrains Mono', monospace !important; }
    [data-testid="stSidebar"] { background-color: #F5F5F5; border-right: 1px solid #E0E0E0; }
    [data-testid="stSidebar"] .stMarkdown h3 { color: #0066CC !important; font-size: 0.85rem; text-transform: uppercase; border-bottom: 2px solid #0066CC; padding-bottom: 0.5rem; margin-top: 1.5rem; }
    .section-divider { border: none; height: 1px; background: #E0E0E0; margin: 1.5rem 0; }
    .info-box { background: #E6F0FA; border-left: 4px solid #0066CC; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    .success-box { background: #E8F5E9; border-left: 4px solid #28A745; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    .warning-box { background: #FFF3E0; border-left: 4px solid #FF9800; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stMetricValue"] { color: #0066CC !important; }
</style>
""", unsafe_allow_html=True)

# Default values from Q3 2025
DEFAULT_VALUES = {
    'trading_commission': 310_195, 'investment_income': 165_348, 'investment_deposits': 4_134_622,
    'investments_amortised_cost': 367_717, 'total_traded_value': 165_000_000, 'period_months': 9,
    'trading_days': 252, 'avg_interest_rate': 5.0, 'commission_rate_bps': 25.0
}

def parse_financial_statement_pdf(uploaded_file):
    try:
        import pdfplumber
    except ImportError:
        st.error("pdfplumber not available")
        return None
    data = {'trading_commission_fees': None, 'investment_income': None, 'investment_deposits': None,
            'investments_amortised_cost': None, 'period_months': 9, 'parse_success': False, 'extracted_items': []}
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = "".join([p.extract_text() or "" for p in pdf.pages])
            for pattern in [r'Trading commission fees\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)', r'Trading commission fees[^\d]+([\d,]+)']:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    val = match.group(3 if len(match.groups()) >= 4 else 1).replace(',', '')
                    data['trading_commission_fees'] = float(val)
                    data['extracted_items'].append(f"Trading Commission: AED {float(val):,.0f}K")
                    break
            for pattern in [r'Investment income\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)', r'Investment income[^\d]+([\d,]+)']:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    val = match.group(3 if len(match.groups()) >= 4 else 1).replace(',', '')
                    data['investment_income'] = float(val)
                    data['extracted_items'].append(f"Investment Income: AED {float(val):,.0f}K")
                    break
            match = re.search(r'Investment deposits[^\d]+([\d,]+)', full_text, re.IGNORECASE)
            if match:
                data['investment_deposits'] = float(match.group(1).replace(',', ''))
                data['extracted_items'].append(f"Investment Deposits: AED {data['investment_deposits']:,.0f}K")
            match = re.search(r'Investments at amortised cost[^\d]+([\d,]+)', full_text, re.IGNORECASE)
            if match:
                data['investments_amortised_cost'] = float(match.group(1).replace(',', ''))
                data['extracted_items'].append(f"Sukuks: AED {data['investments_amortised_cost']:,.0f}K")
            if 'nine-month' in full_text.lower(): data['period_months'] = 9
            elif 'six-month' in full_text.lower(): data['period_months'] = 6
            elif 'three-month' in full_text.lower(): data['period_months'] = 3
            elif 'year ended' in full_text.lower(): data['period_months'] = 12
            data['parse_success'] = len(data['extracted_items']) > 0
    except Exception as e:
        st.error(f"PDF Error: {e}")
    return data

def parse_bulletin_excel(uploaded_file):
    data = {'total_traded_value': None, 'parse_success': False, 'extracted_items': []}
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=1)
        tv_col = next((c for c in df.columns if 'trade value' in str(c).lower()), None)
        if tv_col is None: return data
        df['TV_Clean'] = pd.to_numeric(df[tv_col].astype(str).str.replace(',', ''), errors='coerce')
        name_col = next((c for c in df.columns if any(x in str(c).lower() for x in ['symbol', 'security', 'name'])), df.columns[0])
        for pattern in ['Market Grand Total', 'Market Trades Total', 'Shares Grand Total']:
            mask = df[name_col].astype(str).str.contains(pattern, case=False, na=False)
            if mask.any():
                val = df[mask].iloc[0]['TV_Clean']
                if pd.notna(val) and val > 0:
                    data['total_traded_value'] = float(val)
                    data['extracted_items'].append(f"Traded Value: AED {val:,.0f}")
                    data['parse_success'] = True
                    break
    except Exception as e:
        st.error(f"Excel Error: {e}")
    return data

def safe_val(v, d, mn=None, mx=None):
    if v is None: return d
    try:
        v = float(v)
        if mn and v < mn: return d
        if mx and v > mx: return d
        return v
    except: return d

def fmt_m(v): return f"AED {v/1000:,.1f}M" if v else "N/A"
def fmt_b(v): return f"AED {v/1000000:,.1f}B" if v else "N/A"
def calc_comm(tv, bps): return tv * (bps / 10000) if tv and bps and tv > 0 and bps > 0 else 0
def calc_inv(port, rate): return port * (rate / 100) if port and rate and port > 0 and rate >= 0 else 0

def main():
    st.markdown('<p class="main-header">📊 DFM Scenario Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Dubai Financial Market | Earnings Sensitivity Tool</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("## 📁 Data Sources")
        st.markdown("### Financial Statement")
        fs_file = st.file_uploader("Upload PDF", type=['pdf'], key="fs")
        st.markdown("### Market Bulletin")
        bul_file = st.file_uploader("Upload Excel", type=['xlsx', 'xls'], key="bul")
        st.markdown("---")
        st.markdown("### ⚙️ Manual Override")
        use_manual = st.checkbox("Enable manual entry", value=False)
    
    fs_data = parse_financial_statement_pdf(fs_file) if fs_file else None
    bul_data = parse_bulletin_excel(bul_file) if bul_file else None
    
    d = DEFAULT_VALUES.copy()
    if fs_data and fs_data.get('parse_success'):
        d['trading_commission'] = safe_val(fs_data.get('trading_commission_fees'), d['trading_commission'], 1000)
        d['investment_income'] = safe_val(fs_data.get('investment_income'), d['investment_income'], 1000)
        d['investment_deposits'] = safe_val(fs_data.get('investment_deposits'), d['investment_deposits'], 100000)
        d['investments_amortised_cost'] = safe_val(fs_data.get('investments_amortised_cost'), d['investments_amortised_cost'], 10000)
        d['period_months'] = fs_data.get('period_months', 9)
    if bul_data and bul_data.get('parse_success'):
        d['total_traded_value'] = safe_val(bul_data.get('total_traded_value'), d['total_traded_value'], 1_000_000)
    
    d['total_investment_portfolio'] = d['investment_deposits'] + d['investments_amortised_cost']
    d['adtv'] = d['total_traded_value'] / d['trading_days']
    d['trading_commission_annual'] = d['trading_commission'] * (12 / d['period_months'])
    d['investment_income_annual'] = d['investment_income'] * (12 / d['period_months'])
    if d['total_traded_value'] > 0 and d['trading_commission_annual'] > 0:
        d['commission_rate_bps'] = safe_val((d['trading_commission_annual'] / d['total_traded_value']) * 10000, 25.0, 1.0, 100.0)
    
    if use_manual:
        with st.sidebar:
            d['trading_commission'] = st.number_input("Trading Comm (AED'000)", value=float(d['trading_commission']), min_value=0.0, step=1000.0)
            d['investment_income'] = st.number_input("Inv Income (AED'000)", value=float(d['investment_income']), min_value=0.0, step=1000.0)
            d['total_investment_portfolio'] = st.number_input("Portfolio (AED'000)", value=float(d['total_investment_portfolio']), min_value=0.0, step=10000.0)
            d['total_traded_value'] = st.number_input("Traded Value (AED'000)", value=float(d['total_traded_value']), min_value=1000000.0, step=1000000.0)
            d['commission_rate_bps'] = st.number_input("Comm Rate (bps)", value=float(d['commission_rate_bps']), min_value=1.0, max_value=100.0, step=0.5)
            d['adtv'] = d['total_traded_value'] / d['trading_days']
            d['trading_commission_annual'] = d['trading_commission'] * (12 / d['period_months'])
            d['investment_income_annual'] = d['investment_income'] * (12 / d['period_months'])
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if fs_file and fs_data and fs_data.get('parse_success'):
            st.markdown(f'<div class="success-box"><strong>✅ Financial Statement Loaded</strong><br>{"<br>".join(fs_data["extracted_items"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box"><strong>⚠️ No Financial Statement</strong><br>Using Q3 2025 defaults</div>', unsafe_allow_html=True)
    with c2:
        if bul_file and bul_data and bul_data.get('parse_success'):
            st.markdown(f'<div class="success-box"><strong>✅ Bulletin Loaded</strong><br>{"<br>".join(bul_data["extracted_items"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box"><strong>⚠️ No Bulletin</strong><br>Using 2025 defaults</div>', unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📋 Baseline Metrics")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card-highlight"><div class="metric-label">Trading Commission ({d["period_months"]}M)</div><div class="metric-value-blue">{fmt_m(d["trading_commission"])}</div><div style="color:#666;font-size:0.75rem">Annual: {fmt_m(d["trading_commission_annual"])}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card-highlight"><div class="metric-label">Avg Daily Traded Value</div><div class="metric-value-blue">{fmt_m(d["adtv"])}</div><div style="color:#666;font-size:0.75rem">Total: {fmt_b(d["total_traded_value"])}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card-highlight"><div class="metric-label">Investment Portfolio</div><div class="metric-value-blue">{fmt_b(d["total_investment_portfolio"])}</div><div style="color:#666;font-size:0.75rem">Deposits + Sukuks</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card-highlight"><div class="metric-label">Investment Income ({d["period_months"]}M)</div><div class="metric-value-blue">{fmt_m(d["investment_income"])}</div><div style="color:#666;font-size:0.75rem">Annual: {fmt_m(d["investment_income_annual"])}</div></div>', unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📉 Commission Fee", "📊 Traded Value", "💰 Interest Rate", "🔄 Combined"])
    
    safe_rate = max(1.0, min(50.0, d['commission_rate_bps']))
    
    with tab1:
        st.markdown("### Commission Fee Scenario")
        ci, cr = st.columns([1, 2])
        with ci:
            tv1 = st.number_input("Traded Value (AED B)", 10.0, 500.0, max(10.0, d['total_traded_value']/1e6), 5.0, key="t1tv") * 1e6
            cur_rate = st.number_input("Current Rate (bps)", 1.0, 50.0, safe_rate, 0.5, key="t1cr")
            new_rate = st.number_input("New Rate (bps)", 1.0, 50.0, 20.0, 0.5, key="t1nr")
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
    
    with tab2:
        st.markdown("### Traded Value Scenario")
        ci, cr = st.columns([1, 2])
        with ci:
            method = st.radio("Method", ["ADTV × 252", "Total Annual"], key="t2m")
            if method == "ADTV × 252":
                def_adtv = max(100, d['adtv']/1000)
                cur_adtv = st.number_input("Current ADTV (AED M)", 100.0, 5000.0, def_adtv, 50.0, key="t2ca")
                new_adtv = st.number_input("New ADTV (AED M)", 100.0, 5000.0, def_adtv*0.75, 50.0, key="t2na")
                cur_ann, new_ann = cur_adtv*1000*252, new_adtv*1000*252
            else:
                def_ann = max(50, d['total_traded_value']/1e6)
                cur_ann = st.number_input("Current (AED B)", 50.0, 500.0, def_ann, 5.0, key="t2cb") * 1e6
                new_ann = st.number_input("New (AED B)", 50.0, 500.0, def_ann*0.75, 5.0, key="t2nb") * 1e6
            rate2 = st.number_input("Comm Rate (bps)", 1.0, 50.0, safe_rate, 0.5, key="t2r")
        with cr:
            cur_c2, new_c2 = calc_comm(cur_ann, rate2), calc_comm(new_ann, rate2)
            chg2 = new_c2 - cur_c2
            tv_pct = ((new_ann-cur_ann)/cur_ann*100) if cur_ann > 0 else 0
            c_pct = (chg2/cur_c2*100) if cur_c2 > 0 else 0
            m1, m2, m3 = st.columns(3)
            m1.metric("Current TV", fmt_b(cur_ann))
            m2.metric("New TV", fmt_b(new_ann), f"{tv_pct:+.1f}%")
            m3.metric("Commission Δ", fmt_m(chg2), f"{c_pct:+.1f}%", delta_color="normal" if chg2 >= 0 else "inverse")
            st.dataframe(pd.DataFrame({'Metric': ['Traded Value', 'ADTV', 'Commission'], 'Current': [fmt_b(cur_ann), fmt_m(cur_ann/252), fmt_m(cur_c2)], 'Scenario': [fmt_b(new_ann), fmt_m(new_ann/252), fmt_m(new_c2)], 'Change': [f"{tv_pct:+.1f}%", f"{tv_pct:+.1f}%", f"{fmt_m(chg2)}"]}), hide_index=True)
    
    with tab3:
        st.markdown("### Interest Rate Scenario")
        ci, cr = st.columns([1, 2])
        with ci:
            port = st.number_input("Portfolio (AED B)", 1.0, 20.0, max(1.0, d['total_investment_portfolio']/1e6), 0.1, key="t3p") * 1e6
            cur_ir = st.number_input("Current Rate (%)", 0.0, 15.0, 5.0, 0.25, key="t3cr")
            ir_chg = st.selectbox("Rate Change", ["+50 bps", "+25 bps", "No change", "-25 bps", "-50 bps", "-100 bps", "-150 bps"], index=4, key="t3c")
            chg_map = {"+50 bps": 50, "+25 bps": 25, "No change": 0, "-25 bps": -25, "-50 bps": -50, "-100 bps": -100, "-150 bps": -150}
            new_ir = max(0, cur_ir + chg_map[ir_chg]/100)
            st.info(f"New Rate: **{new_ir:.2f}%**")
        with cr:
            cur_inv, new_inv = calc_inv(port, cur_ir), calc_inv(port, new_ir)
            inv_chg = new_inv - cur_inv
            inv_pct = (inv_chg/cur_inv*100) if cur_inv > 0 else 0
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Income", fmt_m(cur_inv), f"@ {cur_ir:.2f}%")
            m2.metric("New Income", fmt_m(new_inv), f"@ {new_ir:.2f}%")
            m3.metric("Impact", fmt_m(inv_chg), f"{inv_pct:+.1f}%", delta_color="normal" if inv_chg >= 0 else "inverse")
            st.markdown(f'<div class="info-box"><strong>Calculation:</strong><br>Portfolio {fmt_b(port)} × {chg_map[ir_chg]:+d} bps = <strong>{fmt_m(inv_chg)}</strong></div>', unsafe_allow_html=True)
            sens = [{'Rate Δ': f"{r:+d} bps", 'New Rate': f"{max(0,cur_ir+r/100):.2f}%", 'Income': fmt_m(calc_inv(port, max(0,cur_ir+r/100))), 'Impact': fmt_m(calc_inv(port, max(0,cur_ir+r/100))-cur_inv)} for r in [100,50,25,0,-25,-50,-100,-150,-200]]
            st.dataframe(pd.DataFrame(sens), hide_index=True)
    
    with tab4:
        st.markdown("### Combined Scenario")
        cl, cr = st.columns(2)
        with cl:
            st.markdown("#### Inputs")
            ctv = st.number_input("Traded Value (AED B)", 50.0, 500.0, max(50, d['total_traded_value']/1e6), 5.0, key="t4tv") * 1e6
            ccr = st.number_input("Comm Rate (bps)", 1.0, 50.0, safe_rate, 0.5, key="t4cr")
            cport = st.number_input("Portfolio (AED B)", 1.0, 20.0, max(1, d['total_investment_portfolio']/1e6), 0.1, key="t4p") * 1e6
            cir = st.number_input("Interest Rate (%)", 0.0, 15.0, 5.0, 0.25, key="t4ir")
        with cr:
            st.markdown("#### Results")
            sc_comm = calc_comm(ctv, ccr)
            sc_inv = calc_inv(cport, cir)
            sc_tot = sc_comm + sc_inv
            bl_comm, bl_inv = d['trading_commission_annual'], d['investment_income_annual']
            bl_tot = bl_comm + bl_inv
            st.dataframe(pd.DataFrame({'Stream': ['Trading Commission', 'Investment Income', 'TOTAL'], 'Baseline': [fmt_m(bl_comm), fmt_m(bl_inv), fmt_m(bl_tot)], 'Scenario': [fmt_m(sc_comm), fmt_m(sc_inv), fmt_m(sc_tot)], 'Change': [fmt_m(sc_comm-bl_comm), fmt_m(sc_inv-bl_inv), fmt_m(sc_tot-bl_tot)]}), hide_index=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Commission", fmt_m(sc_comm), f"{(sc_comm-bl_comm)/1000:+,.0f}M")
            m2.metric("Investment", fmt_m(sc_inv), f"{(sc_inv-bl_inv)/1000:+,.0f}M")
            m3.metric("Total Δ", fmt_m(sc_tot-bl_tot), f"{(sc_tot-bl_tot)/bl_tot*100:+.1f}%" if bl_tot > 0 else "")
            fig4 = go.Figure(go.Waterfall(orientation="v", measure=["absolute", "relative", "relative", "total"],
                x=["Baseline", "Comm Δ", "Inv Δ", "Scenario"], y=[bl_tot/1000, (sc_comm-bl_comm)/1000, (sc_inv-bl_inv)/1000, sc_tot/1000],
                text=[f"{bl_tot/1000:,.0f}M", f"{(sc_comm-bl_comm)/1000:+,.0f}M", f"{(sc_inv-bl_inv)/1000:+,.0f}M", f"{sc_tot/1000:,.0f}M"],
                textposition="outside", connector={"line": {"color": "#0066CC"}},
                decreasing={"marker": {"color": "#DC3545"}}, increasing={"marker": {"color": "#28A745"}}, totals={"marker": {"color": "#0066CC"}}))
            fig4.update_layout(title="Revenue Bridge", height=350, plot_bgcolor='white', yaxis_title="AED M", showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.caption("**Data:** Upload files or uses Q3 2025 defaults | **Disclaimer:** Internal analysis only")

if __name__ == "__main__":
    main()
