"""
DFM Scenario Analysis Tool v3.4
Dubai Financial Market - Earnings Sensitivity Analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

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
    """Parse financial statement PDF"""
    try:
        import pdfplumber
    except ImportError:
        st.warning("pdfplumber not installed")
        return None
    
    data = {'items': []}
    try:
        with pdfplumber.open(file) as pdf:
            text = "".join([p.extract_text() or "" for p in pdf.pages])
            
            # Trading commission - 9-month figure (value is in AED thousands)
            m = re.search(r'Trading commission fees\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)', text, re.I)
            if m:
                data['trading_commission'] = float(m.group(3).replace(',', ''))
                data['items'].append(f"Trading Comm: {fmt_smart(data['trading_commission'])}")
            
            # Investment income - 9-month figure
            m = re.search(r'Investment income\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)', text, re.I)
            if m:
                data['investment_income'] = float(m.group(3).replace(',', ''))
                data['items'].append(f"Inv Income: {fmt_smart(data['investment_income'])}")
            
            # Investment Portfolio (deposits)
            m = re.search(r'Investment deposits\s+\d+\s+([\d,]+)', text, re.I)
            if m:
                data['investment_deposits'] = float(m.group(1).replace(',', ''))
                data['items'].append(f"Investment Deposits (cash at banks): {fmt_smart(data['investment_deposits'])}")
            
            # Investments at amortised cost (sukuks/bonds)
            m = re.search(r'Investments at amortised cost\s+\d+\s+([\d,]+)', text, re.I)
            if m:
                data['investments_amortised_cost'] = float(m.group(1).replace(',', ''))
                data['items'].append(f"Investments at Amortised Cost (sukuk & bonds): {fmt_smart(data['investments_amortised_cost'])}")
            
            # Period
            if 'nine-month' in text.lower(): data['period_months'] = 9
            elif 'six-month' in text.lower(): data['period_months'] = 6
            elif 'year ended' in text.lower(): data['period_months'] = 12
            else: data['period_months'] = 9
            
    except Exception as e:
        st.error(f"PDF parsing error: {e}")
        return None
    
    return data if data.get('items') else None

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
        for key in ['trading_commission', 'investment_income', 'investment_deposits', 'investments_amortised_cost', 'period_months']:
            if key in fs and fs[key]:
                d[key] = fs[key]
    
    if bul and bul.get('total_traded_value'):
        d['total_traded_value'] = bul['total_traded_value']
    
    # Calculate derived values (all in thousands)
    d['portfolio'] = d['investment_deposits'] + d['investments_amortised_cost']
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
            st.markdown(f'<div class="success-box"><strong>✅ Financial Statement</strong><br>{"<br>".join(fs.get("items", []))}</div>', unsafe_allow_html=True)
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
    c1, c2, c3, c4 = st.columns(4)
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
            <div style="color:#666;font-size:0.75rem">Deposits + Sukuks</div>
        </div>''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''<div class="metric-card-highlight">
            <div class="metric-label">Investment Income ({d["period_months"]}M)</div>
            <div class="metric-value-blue">{fmt_smart(d["investment_income"])}</div>
            <div style="color:#666;font-size:0.75rem">Annual: {fmt_smart(d["inv_annual"])}</div>
        </div>''', unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # ========== SCENARIO TABS ==========
    tab1, tab2, tab3, tab4 = st.tabs(["📉 Commission Fee", "📊 Traded Value", "💰 Interest Rate", "🔄 Combined"])
    
    # ---------- TAB 1: Commission Fee ----------
    with tab1:
        st.markdown("### Commission Fee Scenario")
        st.markdown("*What if trading commission rates change?*")
        
        col_in, col_out = st.columns([1, 2])
        
        with col_in:
            st.markdown("#### Scenario Inputs")
            
            # Convert thousands to billions for user input
            tv_billions = d['total_traded_value'] / 1_000_000
            scenario_tv_b = st.number_input(
                "Annual Traded Value (AED Billions)", 
                min_value=1.0, max_value=1000.0, 
                value=clamp(tv_billions, 1.0, 1000.0, 165.0),
                step=5.0, key="t1_tv"
            )
            scenario_tv = scenario_tv_b * 1_000_000  # Back to thousands
            
            current_rate = st.number_input(
                "Current Rate (bps)", 
                min_value=1.0, max_value=100.0, 
                value=clamp(d['comm_rate'], 1.0, 100.0, 25.0),
                step=0.5, key="t1_cur"
            )
            
            new_rate = st.number_input(
                "New Rate (bps)", 
                min_value=1.0, max_value=100.0, 
                value=20.0, step=0.5, key="t1_new"
            )
        
        with col_out:
            st.markdown("#### Impact Analysis")
            
            curr_comm = calc_comm(scenario_tv, current_rate)
            new_comm = calc_comm(scenario_tv, new_rate)
            diff = new_comm - curr_comm
            pct_str = f"{(diff / curr_comm * 100):+.1f}%" if curr_comm > 0 else "—"
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Income", fmt_smart(curr_comm))
            m2.metric("Scenario Income", fmt_smart(new_comm), f"{new_rate - current_rate:+.1f} bps")
            m3.metric("Annual Impact", fmt_smart(diff), pct_str, delta_color="normal")
            
            # Chart
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Current', x=['Commission Income'], y=[curr_comm/1000], marker_color='#0066CC', text=[fmt_smart(curr_comm)], textposition='outside'))
            fig.add_trace(go.Bar(name='Scenario', x=['Commission Income'], y=[new_comm/1000], marker_color='#66B2FF', text=[fmt_smart(new_comm)], textposition='outside'))
            fig.update_layout(barmode='group', height=300, plot_bgcolor='white', yaxis_title='AED Millions', showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        # ---------- OFFSET CALCULATION ----------
        if new_rate < current_rate and new_rate > 0:
            st.markdown("---")
            st.markdown("#### 📊 Breakeven Analysis: How Much Must Traded Value Increase?")
            
            # Calculate: To maintain current commission with new rate, what traded value is needed?
            # Formula: TV_required = V_current × (current_rate / new_rate)
            tv_required = scenario_tv * (current_rate / new_rate)  # in thousands
            tv_increase_needed = tv_required - scenario_tv  # in thousands
            tv_increase_pct = (tv_increase_needed / scenario_tv * 100) if scenario_tv > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Traded Value", fmt_smart(scenario_tv))
            with col2:
                st.metric("Required Traded Value", fmt_smart(tv_required), "to maintain income")
            with col3:
                st.metric("Volume Increase Needed", fmt_smart(tv_increase_needed), f"+{tv_increase_pct:.1f}%")
            
            # Explanation box
            st.markdown(f'''<div class="info-box">
                <strong>Breakeven Calculation:</strong><br><br>
                To maintain commission income of <strong>{fmt_smart(curr_comm)}</strong> after reducing fees from <strong>{current_rate:.1f} bps</strong> to <strong>{new_rate:.1f} bps</strong>:<br><br>
                • Current: {fmt_smart(scenario_tv)} × {current_rate:.1f} bps = {fmt_smart(curr_comm)}<br>
                • Required: {fmt_smart(tv_required)} × {new_rate:.1f} bps = {fmt_smart(curr_comm)}<br><br>
                <strong>Traded value must increase by {fmt_smart(tv_increase_needed)} (+{tv_increase_pct:.1f}%)</strong> to offset the fee reduction.
            </div>''', unsafe_allow_html=True)
        elif new_rate <= 0:
            st.error("⚠️ New rate must be greater than 0 bps")
    
    # ---------- TAB 2: Traded Value ----------
    with tab2:
        st.markdown("### Traded Value Scenario")
        st.markdown("*What if market trading volumes change?*")
        
        col_in, col_out = st.columns([1, 2])
        
        with col_in:
            st.markdown("#### Scenario Inputs")
            
            input_method = st.radio("Input Method", ["Total Annual Value", "Daily Value × 252"], key="t2_method")
            
            if input_method == "Total Annual Value":
                tv_billions = d['total_traded_value'] / 1_000_000
                cur_tv_b = st.number_input("Current (AED B)", 1.0, 1000.0, clamp(tv_billions, 1.0, 1000.0, 165.0), 5.0, key="t2_cur_tv")
                new_tv_b = st.number_input("Scenario (AED B)", 1.0, 1000.0, clamp(tv_billions * 0.75, 1.0, 1000.0, 125.0), 5.0, key="t2_new_tv")
                cur_tv = cur_tv_b * 1_000_000
                new_tv = new_tv_b * 1_000_000
            else:
                adtv_m = d['adtv'] / 1000  # Convert to millions
                cur_adtv = st.number_input("Current ADTV (AED M)", 100.0, 5000.0, clamp(adtv_m, 100.0, 5000.0, 655.0), 10.0, key="t2_cur_adtv")
                new_adtv = st.number_input("Scenario ADTV (AED M)", 100.0, 5000.0, clamp(adtv_m * 0.75, 100.0, 5000.0, 490.0), 10.0, key="t2_new_adtv")
                cur_tv = cur_adtv * 1000 * 252
                new_tv = new_adtv * 1000 * 252
            
            rate = st.number_input("Commission Rate (bps)", 1.0, 100.0, clamp(d['comm_rate'], 1.0, 100.0, 25.0), 0.5, key="t2_rate")
        
        with col_out:
            st.markdown("#### Impact Analysis")
            
            cur_comm = calc_comm(cur_tv, rate)
            new_comm = calc_comm(new_tv, rate)
            diff = new_comm - cur_comm
            tv_pct_str = f"{((new_tv - cur_tv) / cur_tv * 100):+.1f}%" if cur_tv > 0 else "—"
            comm_pct_str = f"{(diff / cur_comm * 100):+.1f}%" if cur_comm > 0 else "—"
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Current TV", fmt_smart(cur_tv))
            m2.metric("Scenario TV", fmt_smart(new_tv), tv_pct_str)
            m3.metric("Commission Δ", fmt_smart(diff), comm_pct_str, delta_color="normal")
            
            st.dataframe(pd.DataFrame({
                'Metric': ['Traded Value', 'ADTV', 'Commission'],
                'Current': [fmt_smart(cur_tv), fmt_smart(cur_tv/252), fmt_smart(cur_comm)],
                'Scenario': [fmt_smart(new_tv), fmt_smart(new_tv/252), fmt_smart(new_comm)],
                'Change': [tv_pct_str, tv_pct_str, fmt_smart(diff)]
            }), hide_index=True, use_container_width=True)
    
    # ---------- TAB 3: Interest Rate ----------
    with tab3:
        st.markdown("### Interest Rate Scenario")
        st.markdown("*What if interest rates change?*")
        
        col_in, col_out = st.columns([1, 2])
        
        with col_in:
            st.markdown("#### Scenario Inputs")
            
            port_b = d['portfolio'] / 1_000_000
            portfolio = st.number_input("Portfolio (AED B)", 0.5, 20.0, clamp(port_b, 0.5, 20.0, 4.5), 0.1, key="t3_port") * 1_000_000
            
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
            
            port_b = d['portfolio'] / 1_000_000
            comb_port = st.number_input("Portfolio (AED B)", 0.5, 20.0, clamp(port_b, 0.5, 20.0, 4.5), 0.1, key="t4_port") * 1_000_000
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
    
    # Footer
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.caption("**Data:** Upload files for latest data, or uses Q3 2025 defaults | **Disclaimer:** For internal analysis only")

if __name__ == "__main__":
    main()
