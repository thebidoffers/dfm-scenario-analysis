"""
DFM Scenario Analysis Tool
Dubai Financial Market - Earnings Sensitivity Analysis
Based on Q3 2025 Financial Statements

Author: DFM Finance Team
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="DFM Scenario Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --dfm-gold: #C9A227;
        --dfm-gold-light: #E8D48A;
        --dfm-dark: #1A1A2E;
        --dfm-darker: #0F0F1A;
        --dfm-accent: #16213E;
        --dfm-green: #00D26A;
        --dfm-red: #FF6B6B;
        --dfm-blue: #4ECDC4;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--dfm-darker) 0%, var(--dfm-dark) 50%, var(--dfm-accent) 100%);
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    h1, h2, h3 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
    }
    
    p, span, div, label {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, var(--dfm-gold) 0%, var(--dfm-gold-light) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        color: #888;
        font-size: 1rem;
        margin-top: 0.25rem;
        font-weight: 400;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(145deg, rgba(201, 162, 39, 0.1) 0%, rgba(201, 162, 39, 0.05) 100%);
        border: 1px solid rgba(201, 162, 39, 0.2);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
    }
    
    .metric-label {
        color: #999;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.25rem;
    }
    
    .metric-value {
        color: #fff;
        font-size: 1.5rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .metric-change-positive {
        color: var(--dfm-green);
        font-size: 0.875rem;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .metric-change-negative {
        color: var(--dfm-red);
        font-size: 0.875rem;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--dfm-darker) 0%, var(--dfm-accent) 100%);
        border-right: 1px solid rgba(201, 162, 39, 0.2);
    }
    
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--dfm-gold) !important;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-bottom: 1px solid rgba(201, 162, 39, 0.3);
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }
    
    /* Slider styling */
    .stSlider > div > div > div > div {
        background-color: var(--dfm-gold) !important;
    }
    
    /* Section dividers */
    .section-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(201, 162, 39, 0.3) 50%, transparent 100%);
        margin: 2rem 0;
    }
    
    /* Table styling */
    .dataframe {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem;
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(78, 205, 196, 0.1);
        border-left: 3px solid var(--dfm-blue);
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: rgba(255, 107, 107, 0.1);
        border-left: 3px solid var(--dfm-red);
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(201, 162, 39, 0.1);
        border-radius: 8px 8px 0 0;
        border: 1px solid rgba(201, 162, 39, 0.2);
        border-bottom: none;
        color: #999;
        padding: 0.5rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(201, 162, 39, 0.2);
        color: var(--dfm-gold) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# BASELINE FINANCIAL DATA (Q3 2025 Annualized)
# ============================================================================
@st.cache_data
def get_baseline_data():
    """
    Baseline financial data from DFM Q3 2025 Financial Statements
    Values in AED thousands unless otherwise noted
    """
    
    # 9-month actuals from Q3 2025
    q3_data = {
        'trading_commission_fees': 310_195,
        'brokerage_fees': 9_235,
        'clearing_settlement_depositary': 61_843,
        'listing_market_data': 8_806,
        'other_fees': 19_580,
        'investment_income': 165_348,
        'dividend_income': 51_521,
        'other_income': -371,
        'general_admin_expenses': 119_571,
        'amortisation': 42_366,
        'interest_expense': 683,
    }
    
    # Annualize 9-month figures
    annualization_factor = 12 / 9
    
    baseline = {
        # Revenue items (annualized)
        'trading_commission_fees': q3_data['trading_commission_fees'] * annualization_factor,
        'brokerage_fees': q3_data['brokerage_fees'] * annualization_factor,
        'clearing_settlement_depositary': q3_data['clearing_settlement_depositary'] * annualization_factor,
        'listing_market_data': q3_data['listing_market_data'] * annualization_factor,
        'other_fees': q3_data['other_fees'] * annualization_factor,
        'investment_income': q3_data['investment_income'] * annualization_factor,
        'dividend_income': q3_data['dividend_income'] * annualization_factor,
        'other_income': q3_data['other_income'] * annualization_factor,
        
        # Expenses (annualized)
        'general_admin_expenses': q3_data['general_admin_expenses'] * annualization_factor,
        'amortisation': q3_data['amortisation'] * annualization_factor,
        'interest_expense': q3_data['interest_expense'] * annualization_factor,
        
        # Key assumptions
        'traded_value_annual': 165_000_000,  # AED 165 billion in thousands
        'commission_rate_bps': 25.07,  # basis points
        'avg_interest_rate': 5.0,  # percentage
        'interest_earning_assets': 4_502_339,  # AED thousands (deposits + sukuks)
        'corporate_tax_rate': 9.0,  # percentage
        'effective_tax_rate': 8.49,  # percentage (from Q3 2025)
        
        # Trading days
        'trading_days_per_year': 252,
    }
    
    return baseline


def calculate_scenario(baseline, commission_change_bps=0, adtv_change_pct=0, interest_rate_change_bps=0):
    """
    Calculate financial impact of scenario changes
    
    Parameters:
    - commission_change_bps: Change in commission rate (basis points, e.g., -5 = 5bp reduction)
    - adtv_change_pct: Change in average daily traded value (%, e.g., -25 = 25% drop)
    - interest_rate_change_bps: Change in interest rates (basis points, e.g., -25 = 25bp cut)
    
    Returns:
    - Dictionary with scenario financial projections
    """
    
    scenario = baseline.copy()
    
    # -------------------------------------------------------------------------
    # 1. TRADING COMMISSION IMPACT
    # -------------------------------------------------------------------------
    # New commission rate
    new_commission_rate_bps = baseline['commission_rate_bps'] + commission_change_bps
    new_commission_rate_bps = max(0, new_commission_rate_bps)  # Can't go negative
    
    # -------------------------------------------------------------------------
    # 2. ADTV / TRADED VALUE IMPACT
    # -------------------------------------------------------------------------
    # New traded value
    traded_value_multiplier = 1 + (adtv_change_pct / 100)
    new_traded_value = baseline['traded_value_annual'] * traded_value_multiplier
    
    # -------------------------------------------------------------------------
    # 3. RECALCULATE TRADING-RELATED REVENUES
    # -------------------------------------------------------------------------
    # Trading commission = Traded Value × Commission Rate
    scenario['trading_commission_fees'] = new_traded_value * (new_commission_rate_bps / 10000)
    
    # Clearing/Settlement/Depositary - scales with trading volume (assume proportional)
    scenario['clearing_settlement_depositary'] = baseline['clearing_settlement_depositary'] * traded_value_multiplier
    
    # Brokerage fees - partially volume-dependent
    scenario['brokerage_fees'] = baseline['brokerage_fees'] * (0.5 + 0.5 * traded_value_multiplier)
    
    # Other fees - assume 30% volume-dependent
    scenario['other_fees'] = baseline['other_fees'] * (0.7 + 0.3 * traded_value_multiplier)
    
    # -------------------------------------------------------------------------
    # 4. INTEREST RATE IMPACT
    # -------------------------------------------------------------------------
    # New interest rate
    new_interest_rate = baseline['avg_interest_rate'] + (interest_rate_change_bps / 100)
    new_interest_rate = max(0, new_interest_rate)  # Can't go negative
    
    # Investment income scales with interest rate change
    rate_change_multiplier = new_interest_rate / baseline['avg_interest_rate'] if baseline['avg_interest_rate'] > 0 else 1
    scenario['investment_income'] = baseline['investment_income'] * rate_change_multiplier
    
    # -------------------------------------------------------------------------
    # 5. ITEMS ASSUMED UNCHANGED
    # -------------------------------------------------------------------------
    # Listing/market data fees - relatively stable
    scenario['listing_market_data'] = baseline['listing_market_data']
    
    # Dividend income - from strategic investments, not directly affected
    scenario['dividend_income'] = baseline['dividend_income']
    
    # Other income - stable
    scenario['other_income'] = baseline['other_income']
    
    # Expenses - largely fixed costs
    scenario['general_admin_expenses'] = baseline['general_admin_expenses']
    scenario['amortisation'] = baseline['amortisation']
    scenario['interest_expense'] = baseline['interest_expense']
    
    # -------------------------------------------------------------------------
    # 6. CALCULATE TOTALS
    # -------------------------------------------------------------------------
    # Total fee income
    scenario['total_fee_income'] = (
        scenario['trading_commission_fees'] +
        scenario['brokerage_fees'] +
        scenario['clearing_settlement_depositary'] +
        scenario['listing_market_data'] +
        scenario['other_fees']
    )
    
    # Total income
    scenario['total_income'] = (
        scenario['total_fee_income'] +
        scenario['investment_income'] +
        scenario['dividend_income'] +
        scenario['other_income']
    )
    
    # Total expenses
    scenario['total_expenses'] = (
        scenario['general_admin_expenses'] +
        scenario['amortisation'] +
        scenario['interest_expense']
    )
    
    # Profit before tax
    scenario['profit_before_tax'] = scenario['total_income'] - scenario['total_expenses']
    
    # Corporate tax (using effective rate)
    scenario['corporate_tax'] = scenario['profit_before_tax'] * (baseline['effective_tax_rate'] / 100)
    scenario['corporate_tax'] = max(0, scenario['corporate_tax'])  # No negative tax
    
    # Net profit
    scenario['net_profit'] = scenario['profit_before_tax'] - scenario['corporate_tax']
    
    # Store scenario parameters
    scenario['new_commission_rate_bps'] = new_commission_rate_bps
    scenario['new_traded_value'] = new_traded_value
    scenario['new_interest_rate'] = new_interest_rate
    scenario['traded_value_multiplier'] = traded_value_multiplier
    
    return scenario


def calculate_baseline_totals(baseline):
    """Calculate total figures for baseline"""
    baseline['total_fee_income'] = (
        baseline['trading_commission_fees'] +
        baseline['brokerage_fees'] +
        baseline['clearing_settlement_depositary'] +
        baseline['listing_market_data'] +
        baseline['other_fees']
    )
    
    baseline['total_income'] = (
        baseline['total_fee_income'] +
        baseline['investment_income'] +
        baseline['dividend_income'] +
        baseline['other_income']
    )
    
    baseline['total_expenses'] = (
        baseline['general_admin_expenses'] +
        baseline['amortisation'] +
        baseline['interest_expense']
    )
    
    baseline['profit_before_tax'] = baseline['total_income'] - baseline['total_expenses']
    baseline['corporate_tax'] = baseline['profit_before_tax'] * (baseline['effective_tax_rate'] / 100)
    baseline['net_profit'] = baseline['profit_before_tax'] - baseline['corporate_tax']
    
    return baseline


def format_aed(value, in_millions=True):
    """Format value as AED with appropriate suffix"""
    if in_millions:
        return f"AED {value/1000:,.1f}M"
    return f"AED {value:,.0f}K"


def format_change(baseline_val, scenario_val):
    """Format change between baseline and scenario"""
    change = scenario_val - baseline_val
    pct_change = (change / baseline_val * 100) if baseline_val != 0 else 0
    
    if change >= 0:
        return f"+{change/1000:,.1f}M (+{pct_change:.1f}%)", "positive"
    else:
        return f"{change/1000:,.1f}M ({pct_change:.1f}%)", "negative"


# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    # Get baseline data
    baseline = get_baseline_data()
    baseline = calculate_baseline_totals(baseline)
    
    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------
    col_logo, col_title = st.columns([1, 5])
    with col_title:
        st.markdown('<p class="main-header">DFM Scenario Analysis</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Dubai Financial Market | Earnings Sensitivity Tool | Based on Q3 2025 Financials</p>', unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # SIDEBAR - SCENARIO INPUTS
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("## 📊 Scenario Parameters")
        
        st.markdown("### Trading Commission")
        commission_change = st.slider(
            "Commission Rate Change (bps)",
            min_value=-15,
            max_value=10,
            value=0,
            step=1,
            help="Change in trading commission rate. Current rate: ~25 bps"
        )
        st.caption(f"New rate: {baseline['commission_rate_bps'] + commission_change:.1f} bps")
        
        st.markdown("### Average Daily Traded Value")
        adtv_change = st.slider(
            "ADTV Change (%)",
            min_value=-50,
            max_value=50,
            value=0,
            step=5,
            help="Percentage change in average daily traded value"
        )
        new_traded_value = baseline['traded_value_annual'] * (1 + adtv_change/100)
        st.caption(f"New annual traded value: AED {new_traded_value/1000:,.0f}B")
        
        st.markdown("### Interest Rates")
        interest_change = st.selectbox(
            "Interest Rate Change",
            options=[25, 0, -25, -50, -100],
            index=1,
            format_func=lambda x: f"+{x} bps" if x > 0 else f"{x} bps" if x < 0 else "No change",
            help="Change in benchmark interest rates affecting investment income"
        )
        new_rate = baseline['avg_interest_rate'] + (interest_change / 100)
        st.caption(f"New avg rate: {new_rate:.2f}%")
        
        st.markdown("---")
        
        # Quick scenario presets
        st.markdown("### 🎯 Quick Scenarios")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📉 Bear Case", use_container_width=True):
                st.session_state['commission_change'] = -10
                st.session_state['adtv_change'] = -30
                st.session_state['interest_change'] = -100
                st.rerun()
        with col2:
            if st.button("📈 Bull Case", use_container_width=True):
                st.session_state['commission_change'] = 0
                st.session_state['adtv_change'] = 25
                st.session_state['interest_change'] = 0
                st.rerun()
        
        if st.button("🔄 Reset to Baseline", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ Data Source")
        st.caption("Based on DFM Q3 2025 condensed interim consolidated financial statements (9 months ended 30 Sep 2025), annualized.")
        st.caption("Full Year 2025 Traded Value: AED 165B (from Yearly Bulletin)")
    
    # -------------------------------------------------------------------------
    # CALCULATE SCENARIO
    # -------------------------------------------------------------------------
    scenario = calculate_scenario(
        baseline,
        commission_change_bps=commission_change,
        adtv_change_pct=adtv_change,
        interest_rate_change_bps=interest_change
    )
    
    # -------------------------------------------------------------------------
    # KEY METRICS DASHBOARD
    # -------------------------------------------------------------------------
    st.markdown("## 📈 Key Metrics Comparison")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        change_text, change_type = format_change(baseline['total_income'], scenario['total_income'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Income</div>
            <div class="metric-value">{format_aed(scenario['total_income'])}</div>
            <div class="metric-change-{change_type}">{change_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        change_text, change_type = format_change(baseline['total_fee_income'], scenario['total_fee_income'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Fee Income</div>
            <div class="metric-value">{format_aed(scenario['total_fee_income'])}</div>
            <div class="metric-change-{change_type}">{change_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        change_text, change_type = format_change(baseline['profit_before_tax'], scenario['profit_before_tax'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Profit Before Tax</div>
            <div class="metric-value">{format_aed(scenario['profit_before_tax'])}</div>
            <div class="metric-change-{change_type}">{change_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        change_text, change_type = format_change(baseline['net_profit'], scenario['net_profit'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Net Profit</div>
            <div class="metric-value">{format_aed(scenario['net_profit'])}</div>
            <div class="metric-change-{change_type}">{change_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # TABS FOR DETAILED ANALYSIS
    # -------------------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Income Breakdown", "🌊 Waterfall Analysis", "📉 Sensitivity Matrix", "📋 Detailed P&L"])
    
    # TAB 1: Income Breakdown Chart
    with tab1:
        col_chart, col_table = st.columns([2, 1])
        
        with col_chart:
            # Create comparison bar chart
            categories = ['Trading\nCommission', 'Clearing &\nSettlement', 'Investment\nIncome', 'Other\nFees', 'Dividend\nIncome']
            baseline_values = [
                baseline['trading_commission_fees']/1000,
                baseline['clearing_settlement_depositary']/1000,
                baseline['investment_income']/1000,
                (baseline['brokerage_fees'] + baseline['listing_market_data'] + baseline['other_fees'])/1000,
                baseline['dividend_income']/1000
            ]
            scenario_values = [
                scenario['trading_commission_fees']/1000,
                scenario['clearing_settlement_depositary']/1000,
                scenario['investment_income']/1000,
                (scenario['brokerage_fees'] + scenario['listing_market_data'] + scenario['other_fees'])/1000,
                scenario['dividend_income']/1000
            ]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Baseline',
                x=categories,
                y=baseline_values,
                marker_color='rgba(201, 162, 39, 0.6)',
                marker_line_color='rgba(201, 162, 39, 1)',
                marker_line_width=2,
                text=[f'{v:.0f}M' for v in baseline_values],
                textposition='outside',
                textfont=dict(color='#C9A227', size=11)
            ))
            
            fig.add_trace(go.Bar(
                name='Scenario',
                x=categories,
                y=scenario_values,
                marker_color='rgba(78, 205, 196, 0.6)',
                marker_line_color='rgba(78, 205, 196, 1)',
                marker_line_width=2,
                text=[f'{v:.0f}M' for v in scenario_values],
                textposition='outside',
                textfont=dict(color='#4ECDC4', size=11)
            ))
            
            fig.update_layout(
                title=dict(
                    text='Revenue Components: Baseline vs Scenario',
                    font=dict(size=16, color='#fff')
                ),
                barmode='group',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#888'),
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1,
                    font=dict(color='#fff')
                ),
                yaxis=dict(
                    title='AED Millions',
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)'
                ),
                xaxis=dict(
                    tickfont=dict(size=10)
                ),
                height=450,
                margin=dict(t=80, b=50)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col_table:
            st.markdown("#### Revenue Impact Summary")
            
            impact_data = {
                'Component': ['Trading Commission', 'Clearing & Settlement', 'Investment Income', 'Other Fees', 'Dividend Income'],
                'Baseline': [
                    f"AED {baseline['trading_commission_fees']/1000:,.0f}M",
                    f"AED {baseline['clearing_settlement_depositary']/1000:,.0f}M",
                    f"AED {baseline['investment_income']/1000:,.0f}M",
                    f"AED {(baseline['brokerage_fees'] + baseline['listing_market_data'] + baseline['other_fees'])/1000:,.0f}M",
                    f"AED {baseline['dividend_income']/1000:,.0f}M"
                ],
                'Scenario': [
                    f"AED {scenario['trading_commission_fees']/1000:,.0f}M",
                    f"AED {scenario['clearing_settlement_depositary']/1000:,.0f}M",
                    f"AED {scenario['investment_income']/1000:,.0f}M",
                    f"AED {(scenario['brokerage_fees'] + scenario['listing_market_data'] + scenario['other_fees'])/1000:,.0f}M",
                    f"AED {scenario['dividend_income']/1000:,.0f}M"
                ],
                'Change': [
                    f"{(scenario['trading_commission_fees'] - baseline['trading_commission_fees'])/1000:+,.0f}M",
                    f"{(scenario['clearing_settlement_depositary'] - baseline['clearing_settlement_depositary'])/1000:+,.0f}M",
                    f"{(scenario['investment_income'] - baseline['investment_income'])/1000:+,.0f}M",
                    f"{((scenario['brokerage_fees'] + scenario['listing_market_data'] + scenario['other_fees']) - (baseline['brokerage_fees'] + baseline['listing_market_data'] + baseline['other_fees']))/1000:+,.0f}M",
                    f"{(scenario['dividend_income'] - baseline['dividend_income'])/1000:+,.0f}M"
                ]
            }
            
            df_impact = pd.DataFrame(impact_data)
            st.dataframe(df_impact, hide_index=True, use_container_width=True)
    
    # TAB 2: Waterfall Chart
    with tab2:
        # Create waterfall chart showing path from baseline to scenario profit
        waterfall_items = [
            ('Baseline Net Profit', baseline['net_profit']/1000, 'absolute'),
            ('Trading Commission Δ', (scenario['trading_commission_fees'] - baseline['trading_commission_fees'])/1000, 'relative'),
            ('Clearing & Settlement Δ', (scenario['clearing_settlement_depositary'] - baseline['clearing_settlement_depositary'])/1000, 'relative'),
            ('Investment Income Δ', (scenario['investment_income'] - baseline['investment_income'])/1000, 'relative'),
            ('Other Fees Δ', ((scenario['brokerage_fees'] + scenario['listing_market_data'] + scenario['other_fees']) - 
                            (baseline['brokerage_fees'] + baseline['listing_market_data'] + baseline['other_fees']))/1000, 'relative'),
            ('Tax Impact Δ', -(scenario['corporate_tax'] - baseline['corporate_tax'])/1000, 'relative'),
            ('Scenario Net Profit', scenario['net_profit']/1000, 'total')
        ]
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="Net Profit Bridge",
            orientation="v",
            measure=[item[2] for item in waterfall_items],
            x=[item[0] for item in waterfall_items],
            y=[item[1] for item in waterfall_items],
            textposition="outside",
            text=[f"AED {item[1]:,.0f}M" for item in waterfall_items],
            textfont=dict(color='#fff', size=11),
            connector={"line": {"color": "rgba(201, 162, 39, 0.5)", "width": 2}},
            decreasing={"marker": {"color": "#FF6B6B", "line": {"color": "#FF6B6B", "width": 2}}},
            increasing={"marker": {"color": "#00D26A", "line": {"color": "#00D26A", "width": 2}}},
            totals={"marker": {"color": "#C9A227", "line": {"color": "#C9A227", "width": 2}}}
        ))
        
        fig_waterfall.update_layout(
            title=dict(
                text="Net Profit Bridge: Baseline → Scenario",
                font=dict(size=16, color='#fff')
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888'),
            yaxis=dict(
                title='AED Millions',
                gridcolor='rgba(255,255,255,0.1)',
                zerolinecolor='rgba(255,255,255,0.2)'
            ),
            xaxis=dict(tickangle=-30),
            height=500,
            showlegend=False,
            margin=dict(t=80, b=100)
        )
        
        st.plotly_chart(fig_waterfall, use_container_width=True)
        
        # Impact breakdown
        total_impact = scenario['net_profit'] - baseline['net_profit']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trading_impact = (scenario['trading_commission_fees'] - baseline['trading_commission_fees'] + 
                            scenario['clearing_settlement_depositary'] - baseline['clearing_settlement_depositary'])
            st.metric(
                "Trading Activity Impact",
                f"AED {trading_impact/1000:,.0f}M",
                delta=f"{trading_impact/baseline['net_profit']*100:+.1f}% of baseline profit"
            )
        
        with col2:
            interest_impact = scenario['investment_income'] - baseline['investment_income']
            st.metric(
                "Interest Rate Impact",
                f"AED {interest_impact/1000:,.0f}M",
                delta=f"{interest_impact/baseline['net_profit']*100:+.1f}% of baseline profit"
            )
        
        with col3:
            st.metric(
                "Total Net Profit Impact",
                f"AED {total_impact/1000:,.0f}M",
                delta=f"{total_impact/baseline['net_profit']*100:+.1f}% change"
            )
    
    # TAB 3: Sensitivity Matrix
    with tab3:
        st.markdown("#### Net Profit Sensitivity Analysis")
        st.markdown("Shows net profit (AED millions) under different ADTV and Commission Rate scenarios")
        
        # Create sensitivity matrix
        adtv_scenarios = [-40, -30, -20, -10, 0, 10, 20, 30]
        commission_scenarios = [-10, -5, 0, 5]
        
        sensitivity_data = []
        for adtv in adtv_scenarios:
            row = []
            for comm in commission_scenarios:
                result = calculate_scenario(baseline, commission_change_bps=comm, adtv_change_pct=adtv, interest_rate_change_bps=interest_change)
                row.append(result['net_profit']/1000)
            sensitivity_data.append(row)
        
        # Create heatmap
        fig_heat = go.Figure(data=go.Heatmap(
            z=sensitivity_data,
            x=[f"{c:+d} bps" for c in commission_scenarios],
            y=[f"{a:+d}%" for a in adtv_scenarios],
            colorscale=[
                [0, '#FF6B6B'],
                [0.5, '#1A1A2E'],
                [1, '#00D26A']
            ],
            text=[[f'{val:.0f}' for val in row] for row in sensitivity_data],
            texttemplate='%{text}',
            textfont={"size": 12, "color": "#fff"},
            hoverongaps=False,
            hovertemplate='ADTV: %{y}<br>Commission: %{x}<br>Net Profit: AED %{z:.0f}M<extra></extra>'
        ))
        
        fig_heat.update_layout(
            title=dict(
                text=f'Net Profit Sensitivity (Interest Rate: {interest_change:+d} bps)',
                font=dict(size=16, color='#fff')
            ),
            xaxis=dict(title='Commission Rate Change', side='bottom'),
            yaxis=dict(title='ADTV Change'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888'),
            height=450
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Interest rate sensitivity table
        st.markdown("#### Interest Rate Sensitivity")
        st.markdown("Impact on Investment Income under different rate scenarios")
        
        rate_scenarios = [25, 0, -25, -50, -100, -150]
        rate_results = []
        for rate in rate_scenarios:
            result = calculate_scenario(baseline, interest_rate_change_bps=rate)
            rate_results.append({
                'Rate Change': f"{rate:+d} bps",
                'New Rate': f"{baseline['avg_interest_rate'] + rate/100:.2f}%",
                'Investment Income': f"AED {result['investment_income']/1000:,.0f}M",
                'Change': f"AED {(result['investment_income'] - baseline['investment_income'])/1000:+,.0f}M",
                'Net Profit Impact': f"AED {(result['net_profit'] - baseline['net_profit'])/1000:+,.0f}M"
            })
        
        df_rates = pd.DataFrame(rate_results)
        st.dataframe(df_rates, hide_index=True, use_container_width=True)
    
    # TAB 4: Detailed P&L
    with tab4:
        st.markdown("#### Pro Forma Income Statement Comparison")
        
        pl_data = {
            'Line Item': [
                'Trading Commission Fees',
                'Brokerage Fees',
                'Clearing, Settlement & Depositary',
                'Listing & Market Data Fees',
                'Other Fees',
                '**Total Fee Income**',
                '',
                'Investment Income',
                'Dividend Income',
                'Other Income',
                '**Total Income**',
                '',
                'General & Administrative Expenses',
                'Amortisation',
                'Interest Expense',
                '**Total Expenses**',
                '',
                '**Profit Before Tax**',
                'Corporate Tax',
                '**Net Profit**'
            ],
            'Baseline (AED K)': [
                f"{baseline['trading_commission_fees']:,.0f}",
                f"{baseline['brokerage_fees']:,.0f}",
                f"{baseline['clearing_settlement_depositary']:,.0f}",
                f"{baseline['listing_market_data']:,.0f}",
                f"{baseline['other_fees']:,.0f}",
                f"**{baseline['total_fee_income']:,.0f}**",
                '',
                f"{baseline['investment_income']:,.0f}",
                f"{baseline['dividend_income']:,.0f}",
                f"{baseline['other_income']:,.0f}",
                f"**{baseline['total_income']:,.0f}**",
                '',
                f"({baseline['general_admin_expenses']:,.0f})",
                f"({baseline['amortisation']:,.0f})",
                f"({baseline['interest_expense']:,.0f})",
                f"**({baseline['total_expenses']:,.0f})**",
                '',
                f"**{baseline['profit_before_tax']:,.0f}**",
                f"({baseline['corporate_tax']:,.0f})",
                f"**{baseline['net_profit']:,.0f}**"
            ],
            'Scenario (AED K)': [
                f"{scenario['trading_commission_fees']:,.0f}",
                f"{scenario['brokerage_fees']:,.0f}",
                f"{scenario['clearing_settlement_depositary']:,.0f}",
                f"{scenario['listing_market_data']:,.0f}",
                f"{scenario['other_fees']:,.0f}",
                f"**{scenario['total_fee_income']:,.0f}**",
                '',
                f"{scenario['investment_income']:,.0f}",
                f"{scenario['dividend_income']:,.0f}",
                f"{scenario['other_income']:,.0f}",
                f"**{scenario['total_income']:,.0f}**",
                '',
                f"({scenario['general_admin_expenses']:,.0f})",
                f"({scenario['amortisation']:,.0f})",
                f"({scenario['interest_expense']:,.0f})",
                f"**({scenario['total_expenses']:,.0f})**",
                '',
                f"**{scenario['profit_before_tax']:,.0f}**",
                f"({scenario['corporate_tax']:,.0f})",
                f"**{scenario['net_profit']:,.0f}**"
            ],
            'Variance (AED K)': [
                f"{scenario['trading_commission_fees'] - baseline['trading_commission_fees']:+,.0f}",
                f"{scenario['brokerage_fees'] - baseline['brokerage_fees']:+,.0f}",
                f"{scenario['clearing_settlement_depositary'] - baseline['clearing_settlement_depositary']:+,.0f}",
                f"{scenario['listing_market_data'] - baseline['listing_market_data']:+,.0f}",
                f"{scenario['other_fees'] - baseline['other_fees']:+,.0f}",
                f"**{scenario['total_fee_income'] - baseline['total_fee_income']:+,.0f}**",
                '',
                f"{scenario['investment_income'] - baseline['investment_income']:+,.0f}",
                f"{scenario['dividend_income'] - baseline['dividend_income']:+,.0f}",
                f"{scenario['other_income'] - baseline['other_income']:+,.0f}",
                f"**{scenario['total_income'] - baseline['total_income']:+,.0f}**",
                '',
                f"{-(scenario['general_admin_expenses'] - baseline['general_admin_expenses']):+,.0f}",
                f"{-(scenario['amortisation'] - baseline['amortisation']):+,.0f}",
                f"{-(scenario['interest_expense'] - baseline['interest_expense']):+,.0f}",
                f"**{-(scenario['total_expenses'] - baseline['total_expenses']):+,.0f}**",
                '',
                f"**{scenario['profit_before_tax'] - baseline['profit_before_tax']:+,.0f}**",
                f"{-(scenario['corporate_tax'] - baseline['corporate_tax']):+,.0f}",
                f"**{scenario['net_profit'] - baseline['net_profit']:+,.0f}**"
            ]
        }
        
        df_pl = pd.DataFrame(pl_data)
        st.dataframe(df_pl, hide_index=True, use_container_width=True, height=700)
        
        # Assumptions box
        st.markdown("""
        <div class="info-box">
            <strong>Key Assumptions:</strong><br>
            • Trading commission directly scales with traded value × commission rate<br>
            • Clearing & settlement fees scale proportionally with traded value<br>
            • Brokerage fees: 50% fixed, 50% variable with volume<br>
            • Other fees: 70% fixed, 30% variable with volume<br>
            • Investment income scales linearly with interest rate changes<br>
            • Operating expenses treated as fixed costs<br>
            • Tax rate: 8.49% effective (from Q3 2025)
        </div>
        """, unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------------------------
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("**Current Scenario Parameters:**")
        st.caption(f"Commission: {commission_change:+d} bps | ADTV: {adtv_change:+d}% | Interest: {interest_change:+d} bps")
    with col2:
        st.caption("**Data Source:**")
        st.caption("DFM Q3 2025 Financial Statements | Yearly Bulletin 2025")
    with col3:
        st.caption("**Disclaimer:**")
        st.caption("For internal analysis only. Not investment advice.")


if __name__ == "__main__":
    main()
