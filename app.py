"""
DFM Scenario Analysis Tool v4.0 (FS1)
Dubai Financial Market - Earnings & Investment Risk Sensitivity Analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from parsers.pdf_financials import (
    parse_pdf_financials,
    compute_portfolio_from_metrics,
    compute_ear_portfolio,
)

st.set_page_config(page_title="DFM Scenario Analysis", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; }
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    h1, h2, h3, p, span, div, label { font-family: 'Inter', sans-serif !important; color: #1A1A1A; }
    .main-header { color: #0066CC; font-size: 2rem; font-weight: 700; }
    .sub-header { color: #666666; font-size: 0.95rem; }
    .metric-card-highlight { background: #E6F0FA; border: 1px solid #0066CC; border-radius: 8px; padding: 1.25rem; margin: 0.5rem 0; }
    .metric-label { color: #666666; font-size: 0.75rem; text-transform: uppercase; font-weight: 500; }
    .metric-value-blue { color: #0066CC; font-size: 1.5rem; font-weight: 600; font-family: monospace; }
    [data-testid="stSidebar"] { background-color: #F5F5F5; }
    .section-divider { border: none; height: 1px; background: #E0E0E0; margin: 1.5rem 0; }
    .info-box { background: #E6F0FA; border-left: 4px solid #0066CC; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    .success-box { background: #E8F5E9; border-left: 4px solid #28A745; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    .warning-box { background: #FFF3E0; border-left: 4px solid #FF9800; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stMetricValue"] { color: #0066CC !important; }
</style>
""", unsafe_allow_html=True)

# ============ DEFAULTS (Q3 2025, all in AED thousands) ============
DEFAULT = {
    'trading_commission': 310_195,
    'investment_income': 165_348,
    'investment_deposits': 4_134_622,
    'investments_amortised_cost': 367_717,
    'fvtoci': 1_411_836,
    'fvtoci_equity': 1_111_095,
    'fvtoci_funds': 25_146,
    'fvtoci_sukuk': 275_595,
    'dividend_income': 51_521,
    'total_traded_value': 165_000_000,  # AED 165B in thousands
    'period_months': 9,
    'trading_days': 252,
}

def fmt_smart(val_thousands):
    """
    Smart formatting: converts AED thousands to appropriate unit
    Input is in AED thousands
    - >= 1B (1,000,000 thousands) -> show as X.XXB
    - >= 1M (1,000 thousands) -> show as X.XXM  
    - < 1M -> show as X.XXK
    Handles negative numbers for showing impacts/changes
    """
    try:
        v = float(val_thousands)
        if v == 0:
            return "AED 0"
        
        # Handle negative numbers
        sign = ""
        if v < 0:
            sign = "-"
            v = abs(v)
        
        # Convert from thousands to actual AED
        aed = v * 1000
        
        if aed >= 1_000_000_000:  # >= 1 Billion
            return f"{sign}AED {aed / 1_000_000_000:.2f}B"
        elif aed >= 1_000_000:  # >= 1 Million
            return f"{sign}AED {aed / 1_000_000:.2f}M"
        else:  # Thousands
            return f"{sign}AED {aed / 1_000:.2f}K"
    except:
        return "N/A"

def fmt_smart_raw(val_aed):
    """
    Smart formatting for raw AED values (not in thousands)
    """
    try:
        v = float(val_aed)
        if v <= 0:
            return "N/A"
        
        if v >= 1_000_000_000:  # >= 1 Billion
            return f"AED {v / 1_000_000_000:.2f}B"
        elif v >= 1_000_000:  # >= 1 Million
            return f"AED {v / 1_000_000:.2f}M"
        elif v >= 1_000:  # >= 1 Thousand
            return f"AED {v / 1_000:.2f}K"
        else:
            return f"AED {v:.2f}"
    except:
        return "N/A"

def parse_pdf(file):
    """Parse financial statement PDF using the parsers module."""
    try:
        result = parse_pdf_financials(file)
        # Return in the format app.py expects: flat dict with metrics + items
        data = dict(result['metrics'])
        data['items'] = result.get('items', [])
        data['audit'] = result.get('audit', [])
        data['note20'] = result.get('note20', {})
        data['note8'] = result.get('note8', {})
        data['warnings'] = result.get('warnings', [])
        return data if data.get('items') else None
    except Exception as e:
        st.error(f"PDF parsing error: {e}")
        return None

def parse_excel(file):
    """Parse bulletin Excel - returns value in AED thousands"""
    data = {'items': []}
    try:
        df = pd.read_excel(file, sheet_name=0, header=1)
        
        # Find trade value column
        tv_col = None
        for c in df.columns:
            if 'trade value' in str(c).lower():
                tv_col = c
                break
        
        if tv_col is None:
            st.warning("No 'Trade Value' column found")
            return None
        
        # Convert to numeric
        df['TV'] = pd.to_numeric(df[tv_col].astype(str).str.replace(',', ''), errors='coerce')
        
        # Find name column
        name_col = df.columns[0]
        for c in df.columns:
            if any(x in str(c).lower() for x in ['symbol', 'security', 'name']):
                name_col = c
                break
        
        # Look for total row
        for pattern in ['Market Grand Total', 'Market Trades Total', 'Shares Grand Total', 'Grand Total']:
            mask = df[name_col].astype(str).str.contains(pattern, case=False, na=False)
            if mask.any():
                val = df.loc[mask, 'TV'].iloc[0]
                if pd.notna(val) and val > 0:
                    # Bulletin reports in AED (not thousands), so divide by 1000 for internal use
                    if val > 1_000_000_000_000:  # > 1 trillion = definitely in AED
                        data['total_traded_value'] = val / 1000  # Convert to thousands
                    else:
                        data['total_traded_value'] = val / 1000  # Assume AED, convert to thousands
                    
                    # Display the raw value smartly
                    data['items'].append(f"Traded Value: {fmt_smart_raw(val)}")
                    break
        
    except Exception as e:
        st.error(f"Excel parsing error: {e}")
        return None
    
    return data if data.get('items') else None

def calc_comm(tv, bps): 
    """Calculate commission (tv in thousands, returns thousands)"""
    try:
        return float(tv) * float(bps) / 10000 if tv and bps and float(tv) > 0 and float(bps) > 0 else 0
    except:
        return 0

def calc_inv(port, rate): 
    """Calculate investment income (port in thousands, returns thousands)"""
    try:
        return float(port) * float(rate) / 100 if port and rate is not None and float(port) > 0 and float(rate) >= 0 else 0
    except:
        return 0

def clamp(val, min_v, max_v, default):
    """Safely clamp a value between min and max"""
    try:
        v = float(val)
        if v < min_v: return default
        if v > max_v: return default
        return v
    except:
        return default

def main():
    st.markdown('<p class="main-header">📊 DFM Scenario Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Dubai Financial Market | Earnings Sensitivity Tool</p>', unsafe_allow_html=True)
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        st.markdown("## 📁 Data Sources")
        st.markdown("### Financial Statement")
        fs_file = st.file_uploader("Upload PDF", type=['pdf'], key="fs")
        st.markdown("### Market Bulletin")
        bul_file = st.file_uploader("Upload Excel", type=['xlsx', 'xls'], key="bul")
        st.markdown("---")
        st.markdown("### ⚙️ Manual Input")
        use_manual = st.checkbox("Enter values manually", value=False)
    
    # ========== PARSE FILES ==========
    fs = parse_pdf(fs_file) if fs_file else None
    bul = parse_excel(bul_file) if bul_file else None
    
    # ========== BUILD DATA ==========
    d = DEFAULT.copy()
    
    if fs:
        # Copy all extracted metrics into d
        fs_keys = [
            'trading_commission', 'investment_income', 'dividend_income',
            'finance_income', 'investment_deposits', 'investments_amortised_cost',
            'fvtoci', 'fvtoci_equity', 'fvtoci_funds', 'fvtoci_sukuk',
            'cash_and_equivalents', 'period_months',
            'investment_income_deposits', 'investment_income_amortised_cost',
            'investment_income_fvtoci',
        ]
        for key in fs_keys:
            if key in fs and fs[key]:
                d[key] = fs[key]
    
    if bul and bul.get('total_traded_value'):
        d['total_traded_value'] = bul['total_traded_value']
    
    # Calculate derived values (all in thousands)
    d['portfolio'] = d['investment_deposits'] + d['investments_amortised_cost'] + d.get('fvtoci', 0)
    d['ear_portfolio'] = d['investment_deposits'] + d['investments_amortised_cost'] + d.get('fvtoci_sukuk', 0)
    d['adtv'] = d['total_traded_value'] / d['trading_days']
    d['comm_annual'] = d['trading_commission'] * 12 / d['period_months']
    d['inv_annual'] = d['investment_income'] * 12 / d['period_months']
    
    # Commission rate (bps)
    if d['total_traded_value'] > 0 and d['comm_annual'] > 0:
        d['comm_rate'] = d['comm_annual'] / d['total_traded_value'] * 10000
    else:
        d['comm_rate'] = 25.0
    
    # ========== MANUAL OVERRIDE ==========
    if use_manual:
        with st.sidebar:
            st.markdown("#### Enter Values (AED '000)")
            d['trading_commission'] = st.number_input("Trading Commission", value=float(d['trading_commission']), min_value=0.0, format="%.0f")
            d['investment_income'] = st.number_input("Investment Income", value=float(d['investment_income']), min_value=0.0, format="%.0f")
            d['portfolio'] = st.number_input("Portfolio", value=float(d['portfolio']), min_value=0.0, format="%.0f")
            d['total_traded_value'] = st.number_input("Total Traded Value", value=float(d['total_traded_value']), min_value=0.0, format="%.0f")
            d['comm_rate'] = st.number_input("Commission Rate (bps)", value=float(d['comm_rate']), min_value=0.1, max_value=100.0, format="%.1f")
            # Recalculate
            d['adtv'] = d['total_traded_value'] / d['trading_days'] if d['trading_days'] > 0 else 0
            d['comm_annual'] = d['trading_commission'] * 12 / d['period_months']
            d['inv_annual'] = d['investment_income'] * 12 / d['period_months']
    
    # ========== STATUS ==========
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if fs:
            items_html = "<br>".join(fs.get("items", []))
            # Show warnings if any
            warn_html = ""
            for w in fs.get("warnings", []):
                warn_html += f'<br><span style="color:#FF9800">⚠️ {w}</span>'
            st.markdown(f'<div class="success-box"><strong>✅ Financial Statement</strong><br>{items_html}{warn_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box"><strong>⚠️ No FS uploaded</strong><br>Using Q3 2025 defaults</div>', unsafe_allow_html=True)
    with c2:
        if bul:
            st.markdown(f'<div class="success-box"><strong>✅ Bulletin</strong><br>{"<br>".join(bul.get("items", []))}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box"><strong>⚠️ No Bulletin uploaded</strong><br>Using 2025 defaults</div>', unsafe_allow_html=True)
    
    # ========== METRICS ==========
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📋 Baseline Metrics")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f'''<div class="metric-card-highlight">
            <div class="metric-label">Trading Commission ({d["period_months"]}M)</div>
            <div class="metric-value-blue">{fmt_smart(d["trading_commission"])}</div>
            <div style="color:#666;font-size:0.75rem">Annual: {fmt_smart(d["comm_annual"])}</div>
        </div>''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''<div class="metric-card-highlight">
            <div class="metric-label">Avg Daily Traded Value</div>
            <div class="metric-value-blue">{fmt_smart(d["adtv"])}</div>
            <div style="color:#666;font-size:0.75rem">Total: {fmt_smart(d["total_traded_value"])}</div>
        </div>''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''<div class="metric-card-highlight">
            <div class="metric-label">Investment Portfolio</div>
            <div class="metric-value-blue">{fmt_smart(d["portfolio"])}</div>
            <div style="color:#666;font-size:0.75rem">Deposits + AC + FVTOCI</div>
        </div>''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''<div class="metric-card-highlight">
            <div class="metric-label">Investment Income ({d["period_months"]}M)</div>
            <div class="metric-value-blue">{fmt_smart(d["investment_income"])}</div>
            <div style="color:#666;font-size:0.75rem">Annual: {fmt_smart(d["inv_annual"])}</div>
        </div>''', unsafe_allow_html=True)
    with c5:
        div_inc = d.get('dividend_income', 0)
        st.markdown(f'''<div class="metric-card-highlight">
            <div class="metric-label">Dividend Income ({d["period_months"]}M)</div>
            <div class="metric-value-blue">{fmt_smart(div_inc)}</div>
            <div style="color:#666;font-size:0.75rem">FVTOCI equity dividends</div>
        </div>''', unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # ========== SCENARIO TABS ==========
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📉 Commission Fee", "📊 Traded Value", "💰 Interest Rate", "🔄 Combined", "🏦 Investment Risk"])
    
    # ---------- TAB 1: Commission Fee ----------
    with tab1:
        st.markdown("### Commission Fee Scenario")
        st.markdown("*Model fee reductions and calculate the traded value needed to offset the impact*")
        
        # -- Fee Structure (informational) --
        st.markdown("##### DFM Market Fee Structure (ex-VAT)")
        
        fee_col1, fee_col2 = st.columns([2, 1])
        
        with fee_col1:
            # Editable fee components
            st.markdown("Adjust any component to model a fee change:")
            
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                broker_bps = st.number_input("Broker (bps)", 0.0, 50.0, 12.5, 0.5, key="fee_broker")
            with fc2:
                market_bps = st.number_input("Market (bps)", 0.0, 50.0, 5.0, 0.5, key="fee_market")
            with fc3:
                sca_bps = st.number_input("SCA (bps)", 0.0, 50.0, 5.0, 0.5, key="fee_sca")
            with fc4:
                cds_bps = st.number_input("CDS (bps)", 0.0, 50.0, 5.0, 0.5, key="fee_cds")
            
            current_total_bps = 27.5  # fixed: current market total
            new_total_bps = broker_bps + market_bps + sca_bps + cds_bps
            fee_reduction_bps = new_total_bps - current_total_bps
        
        with fee_col2:
            st.markdown(f'''<div class="metric-card-highlight">
                <div class="metric-label">Current Total Fee</div>
                <div class="metric-value-blue">27.5 bps</div>
                <div style="color:#666;font-size:0.75rem;margin-top:0.5rem">New Total Fee</div>
                <div style="color:{'#DC3545' if new_total_bps < current_total_bps else '#28A745' if new_total_bps > current_total_bps else '#0066CC'};font-size:1.5rem;font-weight:600;font-family:monospace">{new_total_bps:.1f} bps</div>
                <div style="color:#666;font-size:0.75rem">{fee_reduction_bps:+.1f} bps change</div>
            </div>''', unsafe_allow_html=True)
        
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        # -- Compute DFM's effective rate --
        tv_billions = d['total_traded_value'] / 1_000_000
        scenario_tv = d['total_traded_value']  # in thousands
        current_dfm_rate = d['comm_rate']  # bps, computed from actuals
        adtv = d['adtv']  # in thousands
        curr_comm = d['comm_annual']  # annualised, in thousands
        
        # DFM's new rate: proportional to total market fee change
        # If total market drops from 27.5 to 20, DFM rate drops by same ratio
        if current_total_bps > 0:
            rate_ratio = new_total_bps / current_total_bps
        else:
            rate_ratio = 1.0
        new_dfm_rate = current_dfm_rate * rate_ratio
        
        # New commission income
        new_comm = calc_comm(scenario_tv, new_dfm_rate)
        diff = new_comm - curr_comm
        pct_change = (diff / curr_comm * 100) if curr_comm > 0 else 0
        
        # -- Impact Analysis --
        st.markdown("##### Impact on DFM Commission Income")
        
        impact_df = pd.DataFrame({
            'Metric': ['Total Market Fee', 'DFM Effective Rate', 'Annual Traded Value', 'ADTV', 'Annual Commission Income'],
            'Current': [
                f"{current_total_bps:.1f} bps",
                f"{current_dfm_rate:.1f} bps",
                fmt_smart(scenario_tv),
                fmt_smart(adtv),
                fmt_smart(curr_comm),
            ],
            'Scenario': [
                f"{new_total_bps:.1f} bps",
                f"{new_dfm_rate:.1f} bps",
                fmt_smart(scenario_tv),
                fmt_smart(adtv),
                fmt_smart(new_comm),
            ],
            'Change': [
                f"{fee_reduction_bps:+.1f} bps",
                f"{new_dfm_rate - current_dfm_rate:+.1f} bps",
                "—",
                "—",
                fmt_smart(diff),
            ],
        })
        st.dataframe(impact_df, hide_index=True, use_container_width=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Commission Income", fmt_smart(curr_comm))
        m2.metric("Scenario Commission Income", fmt_smart(new_comm), f"{fee_reduction_bps:+.1f} bps")
        m3.metric("Annual Impact", fmt_smart(diff), f"{pct_change:+.1f}%", delta_color="normal")
        
        # -- Breakeven ADTV --
        if new_total_bps < current_total_bps and new_dfm_rate > 0:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown("##### Breakeven Analysis: How Much Must Traded Value Increase?")
            
            tv_required = scenario_tv * (current_dfm_rate / new_dfm_rate)
            tv_increase = tv_required - scenario_tv
            tv_increase_pct = (tv_increase / scenario_tv * 100) if scenario_tv > 0 else 0
            
            adtv_required = tv_required / d['trading_days']
            adtv_increase = adtv_required - adtv
            
            be_df = pd.DataFrame({
                'Metric': ['Annual Traded Value', 'Avg Daily Traded Value (ADTV)'],
                'Current': [fmt_smart(scenario_tv), fmt_smart(adtv)],
                'Required': [fmt_smart(tv_required), fmt_smart(adtv_required)],
                'Increase Needed': [
                    f"{fmt_smart(tv_increase)} (+{tv_increase_pct:.1f}%)",
                    f"{fmt_smart(adtv_increase)} (+{tv_increase_pct:.1f}%)",
                ],
            })
            st.dataframe(be_df, hide_index=True, use_container_width=True)
            
            st.markdown(f'''<div class="info-box">
                <strong>To maintain {fmt_smart(curr_comm)} commission income</strong> after a fee cut from {current_total_bps:.1f} to {new_total_bps:.1f} bps:<br><br>
                ADTV must increase from <strong>{fmt_smart(adtv)}</strong> to <strong>{fmt_smart(adtv_required)}</strong> — a <strong>+{tv_increase_pct:.1f}%</strong> increase in market activity.
            </div>''', unsafe_allow_html=True)
        
        elif new_total_bps >= current_total_bps:
            if new_total_bps > current_total_bps:
                st.markdown(f'''<div class="success-box">
                    Fee increase of {fee_reduction_bps:+.1f} bps generates additional commission income of <strong>{fmt_smart(diff)}</strong> per year at current traded value levels.
                </div>''', unsafe_allow_html=True)
    
    # ---------- TAB 2: Traded Value ----------
    with tab2:
        st.markdown("### Traded Value Scenario")
        st.markdown("*Model incremental traded value from strategic drivers using capital × turnover assumptions*")
        
        # ── Baseline ──────────────────────────────────────────────────
        baseline_tv = d['total_traded_value']  # AED'000
        baseline_rate = d['comm_rate']          # bps
        baseline_comm = d['comm_annual']        # AED'000
        has_bulletin = bul is not None
        
        equities_trading_days = st.number_input(
            "Equities trading days per year", 200, 300, int(d.get('trading_days', 252)), 1,
            key="tv_trading_days",
        )
        baseline_adtv = baseline_tv / equities_trading_days if equities_trading_days > 0 else 0  # AED'000
        
        src_tag = "📊 Bulletin" if has_bulletin else "⚠️ Default"
        bl1, bl2, bl3 = st.columns(3)
        bl1.metric("Baseline Annual TV", f"AED {baseline_tv / 1_000_000:.1f}B", src_tag)
        bl2.metric("Baseline ADTV", f"AED {baseline_adtv / 1_000:.1f}M / day", f"{equities_trading_days} trading days")
        bl3.metric("Commission Rate", f"{baseline_rate:.1f} bps", f"Annual income: {fmt_smart(baseline_comm)}")
        
        if not has_bulletin:
            st.warning("No bulletin uploaded — using default baseline. Upload a DFM Trading Bulletin for actual traded value.")
        
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        # ── Section A — Driver Inputs (Capital × Turnover) ────────────
        st.markdown("#### Strategic Growth Drivers")
        st.markdown("*Each driver derives incremental ADTV from its own capital × turnover assumptions. Toggle each driver on/off to include or exclude it from the scenario total.*")
        
        # ===================== Driver 1: New Listed Products =====================
        d1_col, d2_col = st.columns(2)
        
        with d1_col:
            st.markdown('<div class="metric-card-highlight"><div class="metric-label">Driver 1</div>'
                        '<div style="font-weight:600;font-size:1.1rem">New Listed Products</div>'
                        '<div style="color:#666;font-size:0.8rem">ETFs / ETPs / Structured Notes</div></div>',
                        unsafe_allow_html=True)
            
            inc_d1 = st.checkbox("Include in total", value=True, key="tv_inc_d1")
            
            st.caption("**Formula:** ADTV = AUM × Daily Turnover %")
            st.caption("**AUM** — Total assets under management of new products  \n"
                       "**Daily Turnover** — % of AUM that trades each day")
            
            p1c1, p1c2 = st.columns(2)
            with p1c1:
                prod_aum = st.number_input(
                    "AUM (AED M)", 0.0, 500_000.0, 0.0, 50.0,
                    key="tv_prod_aum",
                )
            with p1c2:
                prod_turnover = st.number_input(
                    "Daily turnover (% of AUM)", 0.0, 50.0, 0.5, 0.1,
                    key="tv_prod_turn",
                )
            
            # AUM in AED M → ×1e6 to get AED
            d1_adtv_aed = prod_aum * 1_000_000 * (prod_turnover / 100)
            d1_adtv_thous = d1_adtv_aed / 1000
            d1_annual_thous = d1_adtv_thous * equities_trading_days
            
            if d1_adtv_thous > 0:
                st.markdown(f"**→ ADTV: AED {d1_adtv_thous / 1_000:.1f}M / day  |  Annual: AED {d1_annual_thous / 1_000_000:.1f}B**")
            else:
                st.caption("*Set inputs above to see implied ADTV*")
        
        # ===================== Driver 2: Digital Assets =====================
        with d2_col:
            st.markdown('<div class="metric-card-highlight"><div class="metric-label">Driver 2</div>'
                        '<div style="font-weight:600;font-size:1.1rem">Digital Assets</div>'
                        '<div style="color:#666;font-size:0.8rem">Crypto / tokenised securities</div></div>',
                        unsafe_allow_html=True)
            
            inc_d2 = st.checkbox("Include in total", value=False, key="tv_inc_d2")
            
            st.caption("**Formula:** ADTV = Active Traders × Trades per Day × Avg Trade Size")
            st.caption("**Active Traders** — Number of traders active per day  \n"
                       "**Trades / Day** — Avg number of trades each trader makes per day  \n"
                       "**Avg Trade Size** — Average value of a single trade in AED")
            
            p2c1, p2c2, p2c3 = st.columns(3)
            with p2c1:
                digi_traders = st.number_input(
                    "Active traders", 0, 5_000_000, 0, 500,
                    key="tv_digi_traders",
                )
            with p2c2:
                digi_trades_day = st.number_input(
                    "Trades / trader / day", 0.0, 10_000.0, 2.0, 1.0,
                    key="tv_digi_tpd",
                )
            with p2c3:
                digi_avg_size = st.number_input(
                    "Avg trade size (AED)", 0.0, 10_000_000.0, 5000.0, 1000.0,
                    key="tv_digi_size", format="%.0f",
                )
            
            d2_adtv_aed = digi_traders * digi_trades_day * digi_avg_size
            d2_adtv_thous = d2_adtv_aed / 1000
            d2_annual_thous = d2_adtv_thous * equities_trading_days
            
            if d2_adtv_thous > 0:
                tag = "" if inc_d2 else " *(excluded)*"
                st.markdown(f"**→ ADTV: AED {d2_adtv_thous / 1_000:.1f}M / day  |  Annual: AED {d2_annual_thous / 1_000_000:.1f}B**{tag}")
            else:
                st.caption("*Set inputs above to see implied ADTV*")
        
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        # ===================== Driver 3: SLB + Financing Rails =====================
        d3_col, d4_col = st.columns(2)
        
        with d3_col:
            st.markdown('<div class="metric-card-highlight"><div class="metric-label">Driver 3</div>'
                        '<div style="font-weight:600;font-size:1.1rem">SLB + Financing Rails</div>'
                        '<div style="color:#666;font-size:0.8rem">Securities lending, borrowing, margin</div></div>',
                        unsafe_allow_html=True)
            
            inc_d3 = st.checkbox("Include in total", value=True, key="tv_inc_d3")
            
            st.caption("**Formula:** Loan = Pledged × LTV% → Invested = Loan × Utilisation% → ADTV = Invested × Daily Turnover%")
            st.caption("**Securities Pledged** — Value of securities posted as collateral  \n"
                       "**Loan-to-Value** — % of collateral the lender will lend  \n"
                       "**Utilisation into DFM** — % of the loan used to buy DFM stocks  \n"
                       "**Daily Turnover** — How often the invested capital trades per day")
            
            p3c1, p3c2 = st.columns(2)
            with p3c1:
                slb_pledged = st.number_input(
                    "Securities pledged (AED M)", 0.0, 500_000.0, 0.0, 50.0,
                    key="tv_slb_pledged",
                )
                slb_ltv = st.number_input(
                    "Loan-to-value (%)", 0.0, 100.0, 90.0, 5.0,
                    key="tv_slb_ltv",
                )
            with p3c2:
                slb_util = st.number_input(
                    "Utilisation into DFM (%)", 0.0, 100.0, 50.0, 5.0,
                    key="tv_slb_util",
                )
                slb_daily_turn = st.number_input(
                    "Daily turnover on invested (%)", 0.0, 100.0, 1.0, 0.5,
                    key="tv_slb_turn",
                )
            
            # Chain: Pledged → Loan → Invested in DFM → Daily Turnover
            slb_loan = slb_pledged * 1_000_000 * (slb_ltv / 100)
            slb_invested = slb_loan * (slb_util / 100)
            d3_adtv_aed = slb_invested * (slb_daily_turn / 100)
            d3_adtv_thous = d3_adtv_aed / 1000
            d3_annual_thous = d3_adtv_thous * equities_trading_days
            
            if slb_pledged > 0:
                st.caption(f"Loan: AED {slb_loan / 1e6:.1f}M → Invested in DFM: AED {slb_invested / 1e6:.1f}M")
                st.markdown(f"**→ ADTV: AED {d3_adtv_thous / 1_000:.1f}M / day  |  Annual: AED {d3_annual_thous / 1_000_000:.1f}B**")
            else:
                st.caption("*Set inputs above to see implied ADTV*")
        
        # ===================== Driver 4: Investor Access Expansion =====================
        with d4_col:
            st.markdown('<div class="metric-card-highlight"><div class="metric-label">Driver 4</div>'
                        '<div style="font-weight:600;font-size:1.1rem">Investor Access Expansion</div>'
                        '<div style="color:#666;font-size:0.8rem">New investors, platforms, corridors</div></div>',
                        unsafe_allow_html=True)
            
            inc_d4 = st.checkbox("Include in total", value=True, key="tv_inc_d4")
            
            st.caption("**Formula:** Capital = Investors × Avg Capital → Deployed = Capital × Deploy% → ADTV = Deployed × Turnover%")
            st.caption("**New Active Investors** — Number of new investors entering the market  \n"
                       "**Avg Funded Capital** — Average capital each new investor brings  \n"
                       "**Deployed into DFM** — % of funded capital actually invested in DFM  \n"
                       "**Daily Turnover** — How often deployed capital trades per day")
            
            p4c1, p4c2 = st.columns(2)
            with p4c1:
                acc_investors = st.number_input(
                    "New active investors", 0, 10_000_000, 0, 1000,
                    key="tv_acc_inv",
                )
                acc_capital = st.number_input(
                    "Avg funded capital (AED)", 0.0, 100_000_000.0, 200000.0, 50000.0,
                    key="tv_acc_cap", format="%.0f",
                )
            with p4c2:
                acc_deploy = st.number_input(
                    "Deployed into DFM (%)", 0.0, 100.0, 50.0, 5.0,
                    key="tv_acc_deploy",
                )
                acc_daily_turn = st.number_input(
                    "Daily turnover (%)", 0.0, 100.0, 0.5, 0.1,
                    key="tv_acc_turn",
                )
            
            acc_funded = acc_investors * acc_capital
            acc_deployed = acc_funded * (acc_deploy / 100)
            d4_adtv_aed = acc_deployed * (acc_daily_turn / 100)
            d4_adtv_thous = d4_adtv_aed / 1000
            d4_annual_thous = d4_adtv_thous * equities_trading_days
            
            if acc_investors > 0:
                st.caption(f"Total funded: AED {acc_funded / 1e6:.1f}M → Deployed: AED {acc_deployed / 1e6:.1f}M")
                st.markdown(f"**→ ADTV: AED {d4_adtv_thous / 1_000:.1f}M / day  |  Annual: AED {d4_annual_thous / 1_000_000:.1f}B**")
            else:
                st.caption("*Set inputs above to see implied ADTV*")
        
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        # ===================== Driver 5: New Listings / Free-Float Growth =====================
        d5_col, vol_col = st.columns(2)
        
        with d5_col:
            st.markdown('<div class="metric-card-highlight"><div class="metric-label">Driver 5</div>'
                        '<div style="font-weight:600;font-size:1.1rem">New Listings / Free-Float Growth</div>'
                        '<div style="color:#666;font-size:0.8rem">IPOs, secondary offerings, index inclusion</div></div>',
                        unsafe_allow_html=True)
            
            inc_d5 = st.checkbox("Include in total", value=True, key="tv_inc_d5")
            
            st.caption("**Formula:** Annual TV = Free-Float Mcap × Velocity → ADTV = Annual TV / Trading Days")
            st.caption("**Free-Float Mcap** — Incremental market cap available for trading  \n"
                       "**Turnover Velocity** — Times per year the free-float turns over (0.5× = 50%)")
            
            p5c1, p5c2 = st.columns(2)
            with p5c1:
                ff_mcap = st.number_input(
                    "Incremental free-float mcap (AED M)", 0.0, 500_000.0, 0.0, 100.0,
                    key="tv_ff_mcap",
                )
            with p5c2:
                ff_velocity = st.number_input(
                    "Annual turnover velocity (x)", 0.0, 10.0, 0.5, 0.1,
                    key="tv_ff_vel",
                )
            
            # AED M → ×1e6, annual → daily
            d5_annual_aed = ff_mcap * 1_000_000 * ff_velocity
            d5_adtv_aed = d5_annual_aed / equities_trading_days if equities_trading_days > 0 else 0
            d5_adtv_thous = d5_adtv_aed / 1000
            d5_annual_thous = d5_adtv_thous * equities_trading_days
            
            if ff_mcap > 0:
                st.markdown(f"**→ Annual: AED {d5_annual_thous / 1_000_000:.1f}B  |  ADTV: AED {d5_adtv_thous / 1_000:.1f}M / day**")
            else:
                st.caption("*Set inputs above to see implied ADTV*")
        
        # ===================== Volatility / Market Multiplier =====================
        with vol_col:
            st.markdown('<div class="metric-card-highlight"><div class="metric-label">Market Multiplier</div>'
                        '<div style="font-weight:600;font-size:1.1rem">Volatility / Market Activity</div>'
                        '<div style="color:#666;font-size:0.8rem">Scales total ADTV (baseline + drivers)</div></div>',
                        unsafe_allow_html=True)
            
            st.caption("**This is not a driver.** It multiplies the combined total (baseline + all included drivers) "
                       "to model higher or lower overall market activity.")
            
            vol_multiplier = st.number_input(
                "Multiplier", 0.10, 5.00, 1.00, 0.05,
                key="tv_vol_mult",
                help="1.00 = no change. 1.20 = 20% more activity. 0.80 = 20% lower.",
            )
            
            st.markdown('<div class="info-box">'
                        '<strong>1.00</strong> = no change &nbsp;|&nbsp; '
                        '<strong>1.20</strong> = +20% activity &nbsp;|&nbsp; '
                        '<strong>0.80</strong> = -20% activity'
                        '</div>', unsafe_allow_html=True)
        
        # ── Core Math ─────────────────────────────────────────────────
        # Additive delta: sum only included drivers
        delta_additive = 0.0
        if inc_d1:
            delta_additive += d1_adtv_thous
        if inc_d2:
            delta_additive += d2_adtv_thous
        if inc_d3:
            delta_additive += d3_adtv_thous
        if inc_d4:
            delta_additive += d4_adtv_thous
        if inc_d5:
            delta_additive += d5_adtv_thous
        
        adtv_pre_vol = baseline_adtv + delta_additive  # AED'000/day
        scenario_adtv = adtv_pre_vol * vol_multiplier   # AED'000/day
        
        # Derived volatility impact (for table row)
        delta_adtv_vol = scenario_adtv - adtv_pre_vol  # AED'000/day
        delta_annual_vol = delta_adtv_vol * equities_trading_days  # AED'000/year
        
        scenario_annual_tv = scenario_adtv * equities_trading_days  # AED'000/year
        delta_annual_total = scenario_annual_tv - baseline_tv  # AED'000/year
        
        # Commission
        scenario_comm = calc_comm(scenario_annual_tv, baseline_rate)
        delta_comm = scenario_comm - baseline_comm
        comm_pct = (delta_comm / baseline_comm * 100) if baseline_comm > 0 else 0
        
        # ── Section C — Driver Contribution Breakdown ─────────────────
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("#### Driver Contribution Breakdown")
        
        driver_data = [
            ("New Listed Products",          d1_adtv_thous, d1_annual_thous, inc_d1),
            ("Digital Assets",               d2_adtv_thous, d2_annual_thous, inc_d2),
            ("SLB + Financing Rails",        d3_adtv_thous, d3_annual_thous, inc_d3),
            ("Investor Access Expansion",    d4_adtv_thous, d4_annual_thous, inc_d4),
            ("New Listings / Free-Float",    d5_adtv_thous, d5_annual_thous, inc_d5),
        ]
        
        driver_rows = []
        subtotal_adtv = 0.0
        subtotal_annual = 0.0
        
        for name, adtv_k, annual_k, included in driver_data:
            adtv_m = adtv_k / 1_000
            annual_b = annual_k / 1_000_000
            comm_impact_k = annual_k * baseline_rate / 10000
            comm_impact_m = comm_impact_k / 1_000
            
            if included:
                subtotal_adtv += adtv_k
                subtotal_annual += annual_k
            
            label = name if included else f"{name} *(excluded)*"
            
            driver_rows.append({
                'Driver': label,
                'ADTV (AED M/day)': f"{adtv_m:+,.1f}" if abs(adtv_m) > 0.05 else "—",
                'Annual (AED B/yr)': f"{annual_b:+,.1f}" if abs(annual_b) > 0.05 else "—",
                'Commission (AED M/yr)': f"{comm_impact_m:+,.1f}" if abs(comm_impact_m) > 0.05 and included else "—",
            })
        
        # Subtotal row
        sub_adtv_m = subtotal_adtv / 1_000
        sub_annual_b = subtotal_annual / 1_000_000
        sub_comm_m = subtotal_annual * baseline_rate / 10000 / 1_000
        
        driver_rows.append({
            'Driver': '**Subtotal (included drivers)**',
            'ADTV (AED M/day)': f"{sub_adtv_m:+,.1f}",
            'Annual (AED B/yr)': f"{sub_annual_b:+,.1f}",
            'Commission (AED M/yr)': f"{sub_comm_m:+,.1f}",
        })
        
        # Volatility impact row
        vol_adtv_m = delta_adtv_vol / 1_000
        vol_annual_b = delta_annual_vol / 1_000_000
        vol_comm_m = delta_annual_vol * baseline_rate / 10000 / 1_000
        
        driver_rows.append({
            'Driver': f'Volatility / market activity (x{vol_multiplier:.2f})',
            'ADTV (AED M/day)': f"{vol_adtv_m:+,.1f}" if abs(vol_adtv_m) > 0.05 else "—",
            'Annual (AED B/yr)': f"{vol_annual_b:+,.1f}" if abs(vol_annual_b) > 0.05 else "—",
            'Commission (AED M/yr)': f"{vol_comm_m:+,.1f}" if abs(vol_comm_m) > 0.05 else "—",
        })
        
        # TOTAL row
        total_adtv_m = (scenario_adtv - baseline_adtv) / 1_000
        total_annual_b = delta_annual_total / 1_000_000
        total_comm_m = delta_comm / 1_000
        
        driver_rows.append({
            'Driver': '**TOTAL**',
            'ADTV (AED M/day)': f"{total_adtv_m:+,.1f}",
            'Annual (AED B/yr)': f"{total_annual_b:+,.1f}",
            'Commission (AED M/yr)': f"{total_comm_m:+,.1f}",
        })
        
        st.dataframe(pd.DataFrame(driver_rows), hide_index=True, use_container_width=True)
        
        # ── Section D — Scenario Summary ──────────────────────────────
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("#### Scenario Summary")
        
        k1, k2, k3, k4 = st.columns(4)
        delta_tv_pct = (delta_annual_total / baseline_tv * 100) if baseline_tv > 0 else 0
        k1.metric(
            "Annual Traded Value",
            f"AED {scenario_annual_tv / 1_000_000:.1f}B",
            f"{delta_annual_total / 1_000_000:+.1f}B ({delta_tv_pct:+.1f}%)" if abs(delta_annual_total) > 0.5 else "—",
        )
        k2.metric(
            "ADTV",
            f"AED {scenario_adtv / 1_000:.1f}M / day",
            f"{(scenario_adtv - baseline_adtv) / 1_000:+.1f}M" if abs(scenario_adtv - baseline_adtv) > 0.5 else "—",
        )
        k3.metric(
            "Commission Income",
            fmt_smart(scenario_comm),
            f"{delta_comm / 1_000:+.1f}M ({comm_pct:+.1f}%)" if abs(delta_comm) > 0.5 else "—",
            delta_color="normal",
        )
        k4.metric(
            "Commission Rate",
            f"{baseline_rate:.1f} bps",
            "unchanged",
        )
        
        # Summary table
        sum_df = pd.DataFrame({
            'Metric': ['Annual Traded Value', 'ADTV', 'Annual Commission Income'],
            'Baseline': [
                f"AED {baseline_tv / 1_000_000:.1f}B",
                f"AED {baseline_adtv / 1_000:.1f}M / day",
                fmt_smart(baseline_comm),
            ],
            'Scenario': [
                f"AED {scenario_annual_tv / 1_000_000:.1f}B",
                f"AED {scenario_adtv / 1_000:.1f}M / day",
                fmt_smart(scenario_comm),
            ],
            'Change': [
                f"{delta_annual_total / 1_000_000:+.1f}B ({delta_tv_pct:+.1f}%)" if abs(delta_annual_total) > 0.5 else "—",
                f"{(scenario_adtv - baseline_adtv) / 1_000:+.1f}M / day" if abs(scenario_adtv - baseline_adtv) > 0.5 else "—",
                f"{delta_comm / 1_000:+.1f}M ({comm_pct:+.1f}%)" if abs(delta_comm) > 0.5 else "—",
            ],
        })
        st.dataframe(sum_df, hide_index=True, use_container_width=True)
        
        # Bar chart: Baseline vs Scenario Annual TV
        if abs(delta_annual_total) > 0.5:
            fig_tv = go.Figure()
            
            labels = ['Baseline', 'Scenario']
            values = [baseline_tv / 1_000_000, scenario_annual_tv / 1_000_000]
            colors = ['#0066CC', '#28A745' if delta_annual_total >= 0 else '#DC3545']
            texts = [f"AED {v:.1f}B" for v in values]
            
            fig_tv.add_trace(go.Bar(
                x=labels, y=values,
                marker_color=colors,
                text=texts,
                textposition='outside',
                textfont=dict(size=13),
            ))
            
            y_max = max(values) * 1.15
            fig_tv.update_layout(
                title="Annual Traded Value: Baseline vs Scenario",
                height=380,
                plot_bgcolor='white',
                yaxis_title='AED Billions',
                yaxis=dict(range=[0, y_max]),
                showlegend=False,
            )
            st.plotly_chart(fig_tv, use_container_width=True)
    
    # ---------- TAB 3: Interest Rate ----------
    with tab3:
        st.markdown("### Interest Rate Scenario")
        st.markdown("*What if interest rates change? Uses Earnings-at-Risk portfolio (deposits + amortised cost + FVTOCI sukuk)*")
        
        col_in, col_out = st.columns([1, 2])
        
        with col_in:
            st.markdown("#### Scenario Inputs")
            
            port_b = d['ear_portfolio'] / 1_000_000
            portfolio = st.number_input("EaR Portfolio (AED B)", 0.5, 20.0, clamp(port_b, 0.5, 20.0, 4.9), 0.1, key="t3_port") * 1_000_000
            
            cur_rate = st.number_input("Current Rate (%)", 0.0, 15.0, 5.0, 0.25, key="t3_cur_rate")
            
            rate_chg = st.selectbox("Rate Change", ["+50 bps", "+25 bps", "No change", "-25 bps", "-50 bps", "-100 bps", "-150 bps"], index=4, key="t3_chg")
            chg_map = {"+50 bps": 0.5, "+25 bps": 0.25, "No change": 0, "-25 bps": -0.25, "-50 bps": -0.5, "-100 bps": -1.0, "-150 bps": -1.5}
            new_rate = max(0, cur_rate + chg_map[rate_chg])
            
            st.info(f"New Rate: **{new_rate:.2f}%**")
        
        with col_out:
            st.markdown("#### Impact Analysis")
            
            cur_inc = calc_inv(portfolio, cur_rate)
            new_inc = calc_inv(portfolio, new_rate)
            diff = new_inc - cur_inc
            pct_str = f"{(diff / cur_inc * 100):+.1f}%" if cur_inc > 0 else "—"
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Income", fmt_smart(cur_inc), f"@ {cur_rate:.2f}%")
            m2.metric("Scenario Income", fmt_smart(new_inc), f"@ {new_rate:.2f}%")
            m3.metric("Annual Impact", fmt_smart(diff), pct_str, delta_color="normal")
            
            st.markdown(f'<div class="info-box"><strong>Calculation:</strong><br>{fmt_smart(portfolio)} × {chg_map[rate_chg]*100:+.0f} bps = <strong>{fmt_smart(diff)}</strong> annual impact</div>', unsafe_allow_html=True)
            
            # Sensitivity table
            sens_data = []
            for bp in [100, 50, 25, 0, -25, -50, -100, -150, -200]:
                r = max(0, cur_rate + bp/100)
                inc = calc_inv(portfolio, r)
                sens_data.append({'Rate Δ': f"{bp:+d} bps", 'New Rate': f"{r:.2f}%", 'Income': fmt_smart(inc), 'Impact': fmt_smart(inc - cur_inc)})
            st.dataframe(pd.DataFrame(sens_data), hide_index=True, use_container_width=True)
    
    # ---------- TAB 4: Combined ----------
    with tab4:
        st.markdown("### Combined Scenario")
        st.markdown("*Model multiple changes together*")
        
        col_in, col_out = st.columns([1, 1])
        
        with col_in:
            st.markdown("#### Scenario Inputs")
            
            tv_b = d['total_traded_value'] / 1_000_000
            comb_tv = st.number_input("Traded Value (AED B)", 1.0, 1000.0, clamp(tv_b, 1.0, 1000.0, 165.0), 5.0, key="t4_tv") * 1_000_000
            comb_rate = st.number_input("Comm Rate (bps)", 1.0, 100.0, clamp(d['comm_rate'], 1.0, 100.0, 25.0), 0.5, key="t4_rate")
            
            port_b = d['ear_portfolio'] / 1_000_000
            comb_port = st.number_input("EaR Portfolio (AED B)", 0.5, 20.0, clamp(port_b, 0.5, 20.0, 4.9), 0.1, key="t4_port") * 1_000_000
            comb_ir = st.number_input("Interest Rate (%)", 0.0, 15.0, 5.0, 0.25, key="t4_ir")
        
        with col_out:
            st.markdown("#### Results")
            
            # Scenario values
            sc_comm = calc_comm(comb_tv, comb_rate)
            sc_inv = calc_inv(comb_port, comb_ir)
            sc_total = sc_comm + sc_inv
            
            # Baseline
            bl_comm = d['comm_annual']
            bl_inv = d['inv_annual']
            bl_total = bl_comm + bl_inv
            
            st.dataframe(pd.DataFrame({
                'Revenue': ['Trading Commission', 'Investment Income', 'TOTAL'],
                'Baseline': [fmt_smart(bl_comm), fmt_smart(bl_inv), fmt_smart(bl_total)],
                'Scenario': [fmt_smart(sc_comm), fmt_smart(sc_inv), fmt_smart(sc_total)],
                'Change': [fmt_smart(sc_comm - bl_comm), fmt_smart(sc_inv - bl_inv), fmt_smart(sc_total - bl_total)]
            }), hide_index=True, use_container_width=True)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Commission", fmt_smart(sc_comm), fmt_smart(sc_comm - bl_comm))
            m2.metric("Investment", fmt_smart(sc_inv), fmt_smart(sc_inv - bl_inv))
            tot_pct = ((sc_total - bl_total) / bl_total * 100) if bl_total > 0 else 0
            m3.metric("Total Δ", fmt_smart(sc_total - bl_total), f"{tot_pct:+.1f}%")
            
            # Waterfall
            fig = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["Baseline", "Commission Δ", "Investment Δ", "Scenario"],
                y=[bl_total/1000, (sc_comm-bl_comm)/1000, (sc_inv-bl_inv)/1000, sc_total/1000],
                text=[fmt_smart(bl_total), fmt_smart(sc_comm-bl_comm), fmt_smart(sc_inv-bl_inv), fmt_smart(sc_total)],
                textposition="outside",
                connector={"line": {"color": "#0066CC"}},
                decreasing={"marker": {"color": "#DC3545"}},
                increasing={"marker": {"color": "#28A745"}},
                totals={"marker": {"color": "#0066CC"}}
            ))
            fig.update_layout(title="Revenue Bridge", height=350, plot_bgcolor='white', yaxis_title="AED Millions", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # ---------- TAB 5: Investment Portfolio Risk ----------
    with tab5:
        st.markdown("### Investment Portfolio Risk Analysis")
        st.markdown("*Two complementary risk lenses for DFM's investment portfolio*")
        
        risk_tab1, risk_tab2 = st.tabs(["📈 Earnings Sensitivity (Income)", "📉 Market Value Sensitivity (OCI/P&L)"])
        
        # ========== EARNINGS-AT-RISK (P&L) ==========
        with risk_tab1:
            st.markdown("#### Earnings-at-Risk: If interest rates change, what happens to DFM's investment income?")
            st.markdown("*Only assets generating recurring investment income: deposits, amortised cost (sukuk), FVTOCI debt (sukuk)*")
            
            # -- Extract values --
            dep_bal = d.get('investment_deposits', 0)
            ac_bal = d.get('investments_amortised_cost', 0)
            sukuk_bal = d.get('fvtoci_sukuk', 0)
            ear_total = dep_bal + ac_bal + sukuk_bal
            
            dep_inc = d.get('investment_income_deposits', 0)
            ac_inc = d.get('investment_income_amortised_cost', 0)
            fvtoci_inc = d.get('investment_income_fvtoci', 0)
            total_inc = d.get('investment_income', 0)
            
            pm = d.get('period_months', 12)
            ann_factor = 12 / pm if pm > 0 else 1
            
            # Annualised incomes
            dep_inc_ann = dep_inc * ann_factor
            ac_inc_ann = ac_inc * ann_factor
            fvtoci_inc_ann = fvtoci_inc * ann_factor
            total_inc_ann = total_inc * ann_factor
            
            # Implied yields
            dep_yield = (dep_inc_ann / dep_bal * 100) if dep_bal > 0 else 0
            ac_yield = (ac_inc_ann / ac_bal * 100) if ac_bal > 0 else 0
            sukuk_yield = (fvtoci_inc_ann / sukuk_bal * 100) if sukuk_bal > 0 else 0
            total_yield = (total_inc_ann / ear_total * 100) if ear_total > 0 else 0
            
            # -- Baseline table --
            st.markdown("##### Current Baseline (Extracted from Financial Statement)")
            
            ear_df = pd.DataFrame({
                'Asset Bucket': ['Investment Deposits', 'Amortised Cost (Sukuk)', 'FVTOCI Debt (Sukuk)', '**TOTAL**'],
                'Balance': [fmt_smart(dep_bal), fmt_smart(ac_bal), fmt_smart(sukuk_bal), fmt_smart(ear_total)],
                'Annual Income': [fmt_smart(dep_inc_ann), fmt_smart(ac_inc_ann), fmt_smart(fvtoci_inc_ann), fmt_smart(total_inc_ann)],
                'Implied Yield': [f"{dep_yield:.2f}%", f"{ac_yield:.2f}%", f"{sukuk_yield:.2f}%", f"{total_yield:.2f}%"],
            })
            st.dataframe(ear_df, hide_index=True, use_container_width=True)
            
            # -- Assumption --
            pct_sensitive = st.slider("% of deposits that are rate-sensitive", 50, 100, 100, 5, key="ear_pct")
            sensitive_deposits = dep_bal * pct_sensitive / 100
            
            # -- Rate shock selector --
            st.markdown("##### Rate Shock Scenario")
            
            shock_bp = st.select_slider(
                "Select rate change (basis points)",
                options=[-200, -150, -100, -50, -25, 0, 25, 50, 100],
                value=-100,
                key="ear_shock",
            )
            
            # Compute per-bucket impact
            dep_delta = sensitive_deposits * shock_bp / 10000
            ac_delta = ac_bal * shock_bp / 10000
            sukuk_delta = sukuk_bal * shock_bp / 10000
            total_delta = dep_delta + ac_delta + sukuk_delta
            
            # New incomes
            dep_new = dep_inc_ann + dep_delta
            ac_new = ac_inc_ann + ac_delta
            fvtoci_new = fvtoci_inc_ann + sukuk_delta
            total_new = total_inc_ann + total_delta
            
            # Pct changes
            dep_pct = (dep_delta / dep_inc_ann * 100) if dep_inc_ann > 0 else 0
            ac_pct = (ac_delta / ac_inc_ann * 100) if ac_inc_ann > 0 else 0
            fvtoci_pct = (sukuk_delta / fvtoci_inc_ann * 100) if fvtoci_inc_ann > 0 else 0
            total_pct = (total_delta / total_inc_ann * 100) if total_inc_ann > 0 else 0
            
            # Scenario table — matches baseline structure
            scenario_df = pd.DataFrame({
                'Asset Bucket': ['Investment Deposits', 'Amortised Cost (Sukuk)', 'FVTOCI Debt (Sukuk)', '**TOTAL**'],
                'Current Income': [fmt_smart(dep_inc_ann), fmt_smart(ac_inc_ann), fmt_smart(fvtoci_inc_ann), fmt_smart(total_inc_ann)],
                f'Impact ({shock_bp:+d} bps)': [fmt_smart(dep_delta), fmt_smart(ac_delta), fmt_smart(sukuk_delta), fmt_smart(total_delta)],
                'New Income': [fmt_smart(dep_new), fmt_smart(ac_new), fmt_smart(fvtoci_new), fmt_smart(total_new)],
                'Change': [f"{dep_pct:+.1f}%", f"{ac_pct:+.1f}%", f"{fvtoci_pct:+.1f}%", f"{total_pct:+.1f}%"],
            })
            st.dataframe(scenario_df, hide_index=True, use_container_width=True)
            
            # -- Summary metrics --
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Annual Income", fmt_smart(total_inc_ann))
            m2.metric(f"Income Impact ({shock_bp:+d} bps)", fmt_smart(total_delta), f"{total_pct:+.1f}%", delta_color="normal")
            m3.metric("New Annual Income", fmt_smart(total_new))
            
            # -- Chart: Baseline vs Scenario by bucket --
            fig_ear = go.Figure()
            buckets = ['Deposits', 'Amortised Cost', 'FVTOCI Sukuk', 'Total']
            baseline_vals = [dep_inc_ann / 1000, ac_inc_ann / 1000, fvtoci_inc_ann / 1000, total_inc_ann / 1000]
            scenario_vals = [dep_new / 1000, ac_new / 1000, fvtoci_new / 1000, total_new / 1000]
            
            fig_ear.add_trace(go.Bar(
                name='Current Income',
                x=buckets, y=baseline_vals,
                marker_color='#0066CC',
                text=[fmt_smart(dep_inc_ann), fmt_smart(ac_inc_ann), fmt_smart(fvtoci_inc_ann), fmt_smart(total_inc_ann)],
                textposition='outside',
            ))
            fig_ear.add_trace(go.Bar(
                name=f'After {shock_bp:+d} bps',
                x=buckets, y=scenario_vals,
                marker_color='#DC3545' if shock_bp < 0 else '#28A745',
                text=[fmt_smart(dep_new), fmt_smart(ac_new), fmt_smart(fvtoci_new), fmt_smart(total_new)],
                textposition='outside',
            ))
            fig_ear.update_layout(
                title=f"Investment Income: Current vs {shock_bp:+d} bps Scenario",
                barmode='group',
                height=400,
                plot_bgcolor='white',
                yaxis_title='AED Millions',
            )
            st.plotly_chart(fig_ear, use_container_width=True)
            
            # -- Full sensitivity table (all shocks at once) --
            with st.expander("📋  Full sensitivity table (all rate shocks)"):
                all_shocks = [-200, -150, -100, -50, -25, 0, 25, 50, 100]
                full_sens = []
                for bp in all_shocks:
                    d_dep = sensitive_deposits * bp / 10000
                    d_ac = ac_bal * bp / 10000
                    d_sk = sukuk_bal * bp / 10000
                    d_tot = d_dep + d_ac + d_sk
                    full_sens.append({
                        'Rate Shock': f"{bp:+d} bps",
                        'Deposits Impact': fmt_smart(d_dep),
                        'AC Impact': fmt_smart(d_ac),
                        'Sukuk Impact': fmt_smart(d_sk),
                        'Total Impact': fmt_smart(d_tot),
                        'New Total Income': fmt_smart(total_inc_ann + d_tot),
                        'Change': f"{(d_tot / total_inc_ann * 100):+.1f}%" if total_inc_ann > 0 else "—",
                    })
                st.dataframe(pd.DataFrame(full_sens), hide_index=True, use_container_width=True)
        
        # ========== VALUE-AT-RISK (OCI / P&L) ==========
        with risk_tab2:
            st.markdown("#### Market Value Sensitivity: What happens to OCI/equity if markets move?")
            st.markdown("*Only FVTOCI assets (AED 1.47B) are carried at fair value. Deposits and amortised cost assets (AED 4.58B) are not revalued — no OCI impact.*")
            
            # -- Extracted values display --
            st.markdown("##### Baseline — FVTOCI Portfolio (Extracted from Financial Statement)")
            
            eq_bal = d.get('fvtoci_equity', 0)
            fund_bal = d.get('fvtoci_funds', 0)
            sukuk_bal_v = d.get('fvtoci_sukuk', 0)
            fvtoci_total = d.get('fvtoci', 0)
            equity_exposed = eq_bal + fund_bal
            
            var_df = pd.DataFrame({
                'FVTOCI Category': ['Equity Securities', 'Managed Funds', 'Sukuk (Debt)', '**TOTAL FVTOCI**'],
                'Balance': [fmt_smart(eq_bal), fmt_smart(fund_bal), fmt_smart(sukuk_bal_v), fmt_smart(fvtoci_total)],
                'What Moves It': ['Equity market prices', 'Equity market prices', 'Interest rate changes', '—'],
                'How It Hits OCI': [
                    'Price up/down → OCI gain/loss',
                    'Price up/down → OCI gain/loss',
                    'Rates up → sukuk price down → OCI loss',
                    '—',
                ],
            })
            st.dataframe(var_df, hide_index=True, use_container_width=True)
            
            # -- Assumptions --
            st.markdown("##### Assumptions")
            var_col1, var_col2 = st.columns(2)
            with var_col1:
                duration = st.number_input("FVTOCI sukuk modified duration (years)", 0.5, 10.0, 2.0, 0.5, key="var_dur")
                st.caption("*Duration is not in the PDF — adjust to DFM's actual portfolio WAL*")
            with var_col2:
                st.markdown(f'''<div class="info-box">
                    <strong>Modified duration</strong> measures how much a sukuk's price changes per 1% move in rates.<br>
                    Duration of {duration:.1f} years means: if rates rise 1%, sukuk prices fall ~{duration:.1f}%.
                </div>''', unsafe_allow_html=True)
            
            # -- Equity shock scenarios --
            st.markdown("##### A) Equity Market Shock → OCI Impact")
            st.markdown(f"*Applied to: FVTOCI equity ({fmt_smart(eq_bal)}) + managed funds ({fmt_smart(fund_bal)}) = {fmt_smart(equity_exposed)}*")
            
            eq_shocks = [-30, -20, -10, -5, 0, 5, 10, 20]
            eq_scenarios = []
            for pct in eq_shocks:
                delta = equity_exposed * pct / 100
                new_val = equity_exposed + delta
                eq_scenarios.append({
                    'Equity Market Move': f"{pct:+d}%",
                    'Current Value': fmt_smart(equity_exposed),
                    'OCI Gain / (Loss)': f"{delta:+,.0f}",
                    'New FVTOCI Equity Value': fmt_smart(new_val),
                })
            
            st.dataframe(pd.DataFrame(eq_scenarios), hide_index=True, use_container_width=True)
            
            # -- Rate shock on FVTOCI debt --
            st.markdown("##### B) Interest Rate Shock → FVTOCI Sukuk OCI Impact")
            st.markdown(f"*Applied to: FVTOCI sukuk ({fmt_smart(sukuk_bal_v)}) | Modified duration = {duration:.1f} years*")
            
            rate_shocks = [-200, -100, -50, 0, 50, 100, 200]
            rate_scenarios = []
            for bp in rate_shocks:
                rate_chg_pct = bp / 100  # bps to percentage points
                price_chg_pct = -duration * rate_chg_pct
                oci_delta = sukuk_bal_v * price_chg_pct / 100
                new_val = sukuk_bal_v + oci_delta
                rate_scenarios.append({
                    'Rate Change': f"{bp:+d} bps",
                    'Sukuk Price Change': f"{price_chg_pct:+.1f}%",
                    'OCI Gain / (Loss)': f"{oci_delta:+,.0f}",
                    'New FVTOCI Sukuk Value': fmt_smart(new_val),
                })
            
            st.dataframe(pd.DataFrame(rate_scenarios), hide_index=True, use_container_width=True)
            
            # -- Dynamic Combined Stress Scenario --
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown("##### Combined Stress Scenario")
            
            stress_col1, stress_col2 = st.columns(2)
            with stress_col1:
                eq_shock_pct = st.select_slider(
                    "Equity market shock (%)",
                    options=[-30, -20, -10, -5, 0, 5, 10, 20],
                    value=-20,
                    key="stress_eq",
                )
            with stress_col2:
                rate_shock_bp = st.select_slider(
                    "Interest rate shock (bps)",
                    options=[-200, -100, -50, 0, 50, 100, 200],
                    value=100,
                    key="stress_rate",
                )
            
            # Compute impacts
            eq_stress = equity_exposed * eq_shock_pct / 100
            rate_chg = rate_shock_bp / 100
            price_chg = -duration * rate_chg
            rate_stress = sukuk_bal_v * price_chg / 100
            total_stress = eq_stress + rate_stress
            
            # Summary table
            stress_df = pd.DataFrame({
                'Component': ['FVTOCI Equity + Funds', 'FVTOCI Sukuk (Debt)', '**TOTAL OCI IMPACT**'],
                'Balance': [fmt_smart(equity_exposed), fmt_smart(sukuk_bal_v), fmt_smart(fvtoci_total)],
                'Shock Applied': [f"{eq_shock_pct:+d}% equity", f"{rate_shock_bp:+d} bps rates", "Combined"],
                'OCI Gain / (Loss)': [fmt_smart(eq_stress), fmt_smart(rate_stress), fmt_smart(total_stress)],
            })
            st.dataframe(stress_df, hide_index=True, use_container_width=True)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Equity OCI Impact", fmt_smart(eq_stress), f"{eq_shock_pct:+d}% shock")
            m2.metric("Sukuk OCI Impact", fmt_smart(rate_stress), f"{rate_shock_bp:+d} bps")
            m3.metric("Total OCI Impact", fmt_smart(total_stress))
            
            # Chart with proper margins and label positioning
            fig_var = go.Figure()
            
            bar_labels = [
                f'FVTOCI Equity<br>({eq_shock_pct:+d}% shock)',
                f'FVTOCI Sukuk<br>({rate_shock_bp:+d} bps)',
                'Total OCI Impact',
            ]
            bar_values = [eq_stress / 1000, rate_stress / 1000, total_stress / 1000]
            bar_text = [fmt_smart(eq_stress), fmt_smart(rate_stress), fmt_smart(total_stress)]
            bar_colors = ['#DC3545', '#FF9800', '#0066CC']
            
            fig_var.add_trace(go.Bar(
                x=bar_labels,
                y=bar_values,
                marker_color=bar_colors,
                text=bar_text,
                textposition='outside',
                textfont=dict(size=13),
            ))
            
            # Calculate y-axis range to ensure labels aren't cut off
            min_val = min(bar_values)
            max_val = max(bar_values)
            y_pad = max(abs(min_val), abs(max_val)) * 0.25
            
            fig_var.update_layout(
                title=f"OCI Stress Test: Equity {eq_shock_pct:+d}% + Rates {rate_shock_bp:+d} bps",
                height=420,
                plot_bgcolor='white',
                yaxis_title='AED Millions',
                yaxis=dict(range=[min_val - y_pad, max_val + y_pad]),
                showlegend=False,
                margin=dict(b=80),
            )
            st.plotly_chart(fig_var, use_container_width=True)
    
    # Footer
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.caption("**Data:** Upload files for latest data, or uses Q3 2025 defaults | **Version:** v4.0 (FS1) | **Disclaimer:** For internal analysis only")

if __name__ == "__main__":
    main()
