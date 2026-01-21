"""
DFM Scenario Analysis Tool
Dubai Financial Market - Earnings Sensitivity Analysis
Based on Q3 2025 Financial Statements

Author: DFM Finance Team
Version: 2.0.0
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
# CLEAN CSS STYLING - White background, Blue/Black fonts
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --dfm-blue: #0066CC;
        --dfm-blue-dark: #004C99;
        --dfm-blue-light: #E6F0FA;
        --dfm-black: #1A1A1A;
        --dfm-gray: #666666;
        --dfm-gray-light: #F5F5F5;
        --dfm-white: #FFFFFF;
        --dfm-green: #28A745;
        --dfm-red: #DC3545;
    }
    
    .stApp {
        background-color: var(--dfm-white);
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: var(--dfm-black) !important;
        font-weight: 600 !important;
    }
    
    p, span, div, label {
        font-family: 'Inter', sans-serif !important;
        color: var(--dfm-black);
    }
    
    /* Header styling */
    .main-header {
        color: var(--dfm-blue);
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        color: var(--dfm-gray);
        font-size: 0.95rem;
        margin-top: 0.25rem;
        font-weight: 400;
    }
    
    /* Metric cards */
    .metric-card {
        background: var(--dfm-white);
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    .metric-card-highlight {
        background: var(--dfm-blue-light);
        border: 1px solid var(--dfm-blue);
        border-radius: 8px;
        padding: 1.25rem;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: var(--dfm-gray);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
        font-weight: 500;
    }
    
    .metric-value {
        color: var(--dfm-black);
        font-size: 1.5rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .metric-value-blue {
        color: var(--dfm-blue);
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
        background-color: var(--dfm-gray-light);
        border-right: 1px solid #E0E0E0;
    }
    
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--dfm-blue) !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 2px solid var(--dfm-blue);
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }
    
    /* Section dividers */
    .section-divider {
        border: none;
        height: 1px;
        background: #E0E0E0;
        margin: 1.5rem 0;
    }
    
    /* Info boxes */
    .info-box {
        background: var(--dfm-blue-light);
        border-left: 4px solid var(--dfm-blue);
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        color: var(--dfm-black);
    }
    
    /* Table styling */
    .dataframe {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: var(--dfm-gray-light);
        border-radius: 8px 8px 0 0;
        border: 1px solid #E0E0E0;
        border-bottom: none;
        color: var(--dfm-gray);
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--dfm-white);
        color: var(--dfm-blue) !important;
        border-color: var(--dfm-blue);
        border-bottom: 2px solid var(--dfm-white);
    }
    
    /* Input styling */
    .stNumberInput label, .stSlider label, .stSelectbox label {
        color: var(--dfm-black) !important;
        font-weight: 500;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Override metric styling */
    [data-testid="stMetricValue"] {
        color: var(--dfm-blue) !important;
    }
    
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# BASELINE FINANCIAL DATA (From Q3 2025 Financial Statements)
# ============================================================================
@st.cache_data
def get_baseline_data():
    """
    Baseline financial data from DFM Q3 2025 Financial Statements
    All values in AED thousands unless otherwise noted
    """
    
    # ACTUAL 9-month figures from Q3 2025 (page 5 of financial statements)
    data = {
        # Trading Commission (9 months actual)
        'trading_commission_9m': 310_195,  # AED '000
        
        # Traded Value
        'total_traded_value_2025': 165_000_000,  # AED '000 (AED 165 billion from bulletin)
        'trading_days': 252,
        
        # Investment Income (9 months actual) - page 5
        'investment_income_9m': 165_348,  # AED '000
        
        # Investment Portfolio (from balance sheet - page 4)
        # Investment deposits (Note 9): AED 4,134,622 thousand
        # Investments at amortised cost (Note 8): AED 367,717 thousand  
        # Total interest-earning: ~AED 4.5 billion
        'investment_deposits': 4_134_622,  # AED '000
        'investments_amortised_cost': 367_717,  # AED '000
        
        # Interest rates from notes (page 15)
        # Deposits: 4.40% to 5.50%
        # Sukuks: 2.591% to 5.5%
        'avg_interest_rate': 5.0,  # Approximate weighted average %
    }
    
    # Calculate derived metrics
    data['total_investment_portfolio'] = data['investment_deposits'] + data['investments_amortised_cost']
    data['adtv'] = data['total_traded_value_2025'] / data['trading_days']  # Average Daily Traded Value
    
    # Annualize 9-month figures
    data['trading_commission_annual'] = data['trading_commission_9m'] * (12 / 9)
    data['investment_income_annual'] = data['investment_income_9m'] * (12 / 9)
    
    # Implied commission rate (bps)
    data['commission_rate_bps'] = (data['trading_commission_annual'] / data['total_traded_value_2025']) * 10000
    
    return data


def format_aed_millions(value_thousands):
    """Format AED thousands to millions with M suffix"""
    return f"AED {value_thousands/1000:,.1f}M"


def format_aed_billions(value_thousands):
    """Format AED thousands to billions with B suffix"""
    return f"AED {value_thousands/1000000:,.1f}B"


def calculate_trading_commission_scenario(traded_value, commission_rate_bps):
    """Calculate trading commission based on traded value and rate"""
    return traded_value * (commission_rate_bps / 10000)


def calculate_investment_income_scenario(portfolio_size, interest_rate_pct):
    """Calculate investment income based on portfolio and rate"""
    return portfolio_size * (interest_rate_pct / 100)


# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    # Get baseline data
    baseline = get_baseline_data()
    
    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------
    st.markdown('<p class="main-header">📊 DFM Scenario Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Dubai Financial Market | Earnings Sensitivity Tool | Q3 2025 Financial Data</p>', unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # KEY METRICS (Editable Baseline)
    # -------------------------------------------------------------------------
    st.markdown("### 📋 Baseline Metrics (from Q3 2025 Financials)")
    st.markdown("*These are actual figures from the financial statements. You can override them below.*")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="metric-label">Trading Commission Income (9M Actual)</div>
            <div class="metric-value-blue">{format_aed_millions(baseline['trading_commission_9m'])}</div>
            <div style="color: #666; font-size: 0.75rem;">Annualized: {format_aed_millions(baseline['trading_commission_annual'])}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="metric-label">Average Daily Traded Value</div>
            <div class="metric-value-blue">{format_aed_millions(baseline['adtv'])}</div>
            <div style="color: #666; font-size: 0.75rem;">Total 2025: {format_aed_billions(baseline['total_traded_value_2025'])}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="metric-label">Investment Portfolio Size</div>
            <div class="metric-value-blue">{format_aed_billions(baseline['total_investment_portfolio'])}</div>
            <div style="color: #666; font-size: 0.75rem;">Deposits + Sukuks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="metric-label">Investment Income (9M Actual)</div>
            <div class="metric-value-blue">{format_aed_millions(baseline['investment_income_9m'])}</div>
            <div style="color: #666; font-size: 0.75rem;">Annualized: {format_aed_millions(baseline['investment_income_annual'])}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # SCENARIO ANALYSIS TABS
    # -------------------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📉 Commission Fee Scenario",
        "📊 Traded Value Scenario", 
        "💰 Interest Rate Scenario",
        "🔄 Combined Scenario"
    ])
    
    # =========================================================================
    # TAB 1: COMMISSION FEE SCENARIO
    # =========================================================================
    with tab1:
        st.markdown("### Commission Fee Reduction Scenario")
        st.markdown("*Analyze the impact if trading commission fees are reduced*")
        
        col_input, col_result = st.columns([1, 2])
        
        with col_input:
            st.markdown("#### Inputs")
            
            # Override baseline traded value if desired
            use_custom_traded_value_t1 = st.checkbox("Override traded value", key="t1_override", value=False)
            if use_custom_traded_value_t1:
                custom_traded_value_t1 = st.number_input(
                    "Total Annual Traded Value (AED Billions)",
                    min_value=50.0,
                    max_value=500.0,
                    value=165.0,
                    step=5.0,
                    key="t1_traded_value"
                ) * 1_000_000  # Convert to thousands
            else:
                custom_traded_value_t1 = baseline['total_traded_value_2025']
            
            st.markdown("---")
            
            # Current commission rate
            current_rate = st.number_input(
                "Current Commission Rate (bps)",
                min_value=1.0,
                max_value=50.0,
                value=round(baseline['commission_rate_bps'], 1),
                step=0.5,
                help="Current rate is approximately 25 bps based on Q3 2025 data"
            )
            
            # New commission rate
            new_rate = st.number_input(
                "New Commission Rate (bps)",
                min_value=1.0,
                max_value=50.0,
                value=20.0,
                step=0.5,
                help="Enter the proposed new commission rate"
            )
            
            rate_change = new_rate - current_rate
        
        with col_result:
            st.markdown("#### Impact Analysis")
            
            # Calculate scenarios
            current_commission = calculate_trading_commission_scenario(custom_traded_value_t1, current_rate)
            new_commission = calculate_trading_commission_scenario(custom_traded_value_t1, new_rate)
            commission_change = new_commission - current_commission
            pct_change = (commission_change / current_commission * 100) if current_commission > 0 else 0
            
            # Display results
            res_col1, res_col2, res_col3 = st.columns(3)
            
            with res_col1:
                st.metric(
                    "Current Commission Income",
                    format_aed_millions(current_commission),
                    delta=None
                )
            
            with res_col2:
                st.metric(
                    "New Commission Income",
                    format_aed_millions(new_commission),
                    delta=f"{rate_change:+.1f} bps rate change"
                )
            
            with res_col3:
                delta_color = "normal" if commission_change >= 0 else "inverse"
                st.metric(
                    "Annual Impact",
                    format_aed_millions(commission_change),
                    delta=f"{pct_change:+.1f}%",
                    delta_color=delta_color
                )
            
            # Chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Current',
                x=['Commission Income'],
                y=[current_commission/1000],
                marker_color='#0066CC',
                text=[f'AED {current_commission/1000:,.0f}M'],
                textposition='outside',
                width=0.3
            ))
            
            fig.add_trace(go.Bar(
                name='Scenario',
                x=['Commission Income'],
                y=[new_commission/1000],
                marker_color='#66B2FF',
                text=[f'AED {new_commission/1000:,.0f}M'],
                textposition='outside',
                width=0.3
            ))
            
            fig.update_layout(
                title='Trading Commission: Current vs Scenario',
                yaxis_title='AED Millions',
                barmode='group',
                height=350,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color='#1A1A1A'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor='#E0E0E0')
            
            st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================================
    # TAB 2: TRADED VALUE SCENARIO
    # =========================================================================
    with tab2:
        st.markdown("### Traded Value Change Scenario")
        st.markdown("*Analyze the impact if average daily or total traded value changes*")
        
        col_input, col_result = st.columns([1, 2])
        
        with col_input:
            st.markdown("#### Inputs")
            
            input_method = st.radio(
                "Input Method",
                ["Daily Traded Value × 252 days", "Total Annual Traded Value"],
                key="t2_method"
            )
            
            if input_method == "Daily Traded Value × 252 days":
                current_adtv = st.number_input(
                    "Current ADTV (AED Millions)",
                    min_value=100.0,
                    max_value=5000.0,
                    value=round(baseline['adtv']/1000, 0),  # Convert to millions
                    step=50.0,
                    key="t2_current_adtv"
                )
                
                new_adtv = st.number_input(
                    "New ADTV (AED Millions)",
                    min_value=100.0,
                    max_value=5000.0,
                    value=round(baseline['adtv']/1000 * 0.75, 0),  # Default to 25% drop
                    step=50.0,
                    key="t2_new_adtv"
                )
                
                current_annual = current_adtv * 1000 * 252  # Back to thousands, then annualize
                new_annual = new_adtv * 1000 * 252
                
            else:
                current_annual_input = st.number_input(
                    "Current Annual Traded Value (AED Billions)",
                    min_value=50.0,
                    max_value=500.0,
                    value=165.0,
                    step=5.0,
                    key="t2_current_annual"
                )
                
                new_annual_input = st.number_input(
                    "New Annual Traded Value (AED Billions)",
                    min_value=50.0,
                    max_value=500.0,
                    value=125.0,  # Default to ~25% drop
                    step=5.0,
                    key="t2_new_annual"
                )
                
                current_annual = current_annual_input * 1_000_000  # Convert to thousands
                new_annual = new_annual_input * 1_000_000
            
            st.markdown("---")
            
            commission_rate_t2 = st.number_input(
                "Commission Rate (bps)",
                min_value=1.0,
                max_value=50.0,
                value=round(baseline['commission_rate_bps'], 1),
                step=0.5,
                key="t2_rate"
            )
        
        with col_result:
            st.markdown("#### Impact Analysis")
            
            # Calculate scenarios
            current_commission_t2 = calculate_trading_commission_scenario(current_annual, commission_rate_t2)
            new_commission_t2 = calculate_trading_commission_scenario(new_annual, commission_rate_t2)
            commission_change_t2 = new_commission_t2 - current_commission_t2
            traded_value_change_pct = ((new_annual - current_annual) / current_annual * 100) if current_annual > 0 else 0
            commission_change_pct_t2 = (commission_change_t2 / current_commission_t2 * 100) if current_commission_t2 > 0 else 0
            
            # Display results
            res_col1, res_col2, res_col3 = st.columns(3)
            
            with res_col1:
                st.metric(
                    "Current Traded Value",
                    format_aed_billions(current_annual),
                    delta=None
                )
            
            with res_col2:
                st.metric(
                    "New Traded Value",
                    format_aed_billions(new_annual),
                    delta=f"{traded_value_change_pct:+.1f}%"
                )
            
            with res_col3:
                delta_color = "normal" if commission_change_t2 >= 0 else "inverse"
                st.metric(
                    "Commission Impact",
                    format_aed_millions(commission_change_t2),
                    delta=f"{commission_change_pct_t2:+.1f}%",
                    delta_color=delta_color
                )
            
            # Comparison table
            comparison_data = {
                'Metric': ['Annual Traded Value', 'ADTV (252 days)', 'Commission Income'],
                'Current': [
                    format_aed_billions(current_annual),
                    format_aed_millions(current_annual/252),
                    format_aed_millions(current_commission_t2)
                ],
                'Scenario': [
                    format_aed_billions(new_annual),
                    format_aed_millions(new_annual/252),
                    format_aed_millions(new_commission_t2)
                ],
                'Change': [
                    f"{traded_value_change_pct:+.1f}%",
                    f"{traded_value_change_pct:+.1f}%",
                    f"{format_aed_millions(commission_change_t2)} ({commission_change_pct_t2:+.1f}%)"
                ]
            }
            
            st.dataframe(pd.DataFrame(comparison_data), hide_index=True, use_container_width=True)
            
            # Chart
            fig2 = go.Figure()
            
            categories = ['Traded Value (B)', 'Commission (M)']
            current_vals = [current_annual/1_000_000, current_commission_t2/1000]
            new_vals = [new_annual/1_000_000, new_commission_t2/1000]
            
            fig2.add_trace(go.Bar(
                name='Current',
                x=categories,
                y=current_vals,
                marker_color='#0066CC',
                text=[f'{v:,.0f}' for v in current_vals],
                textposition='outside'
            ))
            
            fig2.add_trace(go.Bar(
                name='Scenario',
                x=categories,
                y=new_vals,
                marker_color='#66B2FF',
                text=[f'{v:,.0f}' for v in new_vals],
                textposition='outside'
            ))
            
            fig2.update_layout(
                title='Traded Value & Commission Impact',
                barmode='group',
                height=350,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color='#1A1A1A'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
            fig2.update_xaxes(showgrid=False)
            fig2.update_yaxes(gridcolor='#E0E0E0')
            
            st.plotly_chart(fig2, use_container_width=True)
    
    # =========================================================================
    # TAB 3: INTEREST RATE SCENARIO
    # =========================================================================
    with tab3:
        st.markdown("### Interest Rate Change Scenario")
        st.markdown("*Analyze the impact on investment income if interest rates change*")
        
        col_input, col_result = st.columns([1, 2])
        
        with col_input:
            st.markdown("#### Inputs")
            
            # Portfolio size
            portfolio_size = st.number_input(
                "Investment Portfolio Size (AED Billions)",
                min_value=1.0,
                max_value=20.0,
                value=round(baseline['total_investment_portfolio']/1_000_000, 2),
                step=0.1,
                help="Current: AED 4.5B (Deposits + Sukuks)"
            ) * 1_000_000  # Convert to thousands
            
            st.markdown("---")
            
            # Current rate
            current_interest_rate = st.number_input(
                "Current Interest Rate (%)",
                min_value=0.0,
                max_value=15.0,
                value=5.0,
                step=0.25,
                help="Approximate current weighted average rate"
            )
            
            # Rate change options
            rate_change_option = st.selectbox(
                "Interest Rate Change",
                ["+50 bps", "+25 bps", "No change", "-25 bps", "-50 bps", "-100 bps", "-150 bps", "Custom"],
                index=4,  # Default to -50 bps
                key="t3_rate_change"
            )
            
            if rate_change_option == "Custom":
                rate_change_bps = st.number_input(
                    "Custom Rate Change (bps)",
                    min_value=-500,
                    max_value=500,
                    value=-100,
                    step=25
                )
            else:
                rate_map = {
                    "+50 bps": 50, "+25 bps": 25, "No change": 0,
                    "-25 bps": -25, "-50 bps": -50, "-100 bps": -100, "-150 bps": -150
                }
                rate_change_bps = rate_map[rate_change_option]
            
            new_interest_rate = current_interest_rate + (rate_change_bps / 100)
            new_interest_rate = max(0, new_interest_rate)  # Can't go negative
            
            st.info(f"New Interest Rate: **{new_interest_rate:.2f}%**")
        
        with col_result:
            st.markdown("#### Impact Analysis")
            
            # Calculate scenarios
            current_investment_income = calculate_investment_income_scenario(portfolio_size, current_interest_rate)
            new_investment_income = calculate_investment_income_scenario(portfolio_size, new_interest_rate)
            income_change = new_investment_income - current_investment_income
            income_change_pct = (income_change / current_investment_income * 100) if current_investment_income > 0 else 0
            
            # Display results
            res_col1, res_col2, res_col3 = st.columns(3)
            
            with res_col1:
                st.metric(
                    "Current Investment Income",
                    format_aed_millions(current_investment_income),
                    delta=f"@ {current_interest_rate:.2f}%"
                )
            
            with res_col2:
                st.metric(
                    "New Investment Income",
                    format_aed_millions(new_investment_income),
                    delta=f"@ {new_interest_rate:.2f}%"
                )
            
            with res_col3:
                delta_color = "normal" if income_change >= 0 else "inverse"
                st.metric(
                    "Annual Impact",
                    format_aed_millions(income_change),
                    delta=f"{income_change_pct:+.1f}%",
                    delta_color=delta_color
                )
            
            # Simple explanation box
            st.markdown(f"""
            <div class="info-box">
                <strong>Calculation:</strong><br>
                Portfolio: {format_aed_billions(portfolio_size)} × Rate Change: {rate_change_bps:+d} bps<br>
                = <strong>{format_aed_millions(income_change)}</strong> annual impact
            </div>
            """, unsafe_allow_html=True)
            
            # Sensitivity table
            st.markdown("#### Rate Sensitivity Table")
            
            rate_scenarios = [100, 50, 25, 0, -25, -50, -100, -150, -200]
            sensitivity_data = []
            
            for rate_chg in rate_scenarios:
                new_rate = current_interest_rate + (rate_chg / 100)
                new_rate = max(0, new_rate)
                new_income = calculate_investment_income_scenario(portfolio_size, new_rate)
                impact = new_income - current_investment_income
                
                sensitivity_data.append({
                    'Rate Change': f"{rate_chg:+d} bps",
                    'New Rate': f"{new_rate:.2f}%",
                    'Investment Income': format_aed_millions(new_income),
                    'Impact': format_aed_millions(impact)
                })
            
            st.dataframe(pd.DataFrame(sensitivity_data), hide_index=True, use_container_width=True)
    
    # =========================================================================
    # TAB 4: COMBINED SCENARIO
    # =========================================================================
    with tab4:
        st.markdown("### Combined Scenario Analysis")
        st.markdown("*Analyze the combined impact of multiple factors changing simultaneously*")
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.markdown("#### Trading Commission Inputs")
            
            comb_traded_value = st.number_input(
                "Annual Traded Value (AED Billions)",
                min_value=50.0,
                max_value=500.0,
                value=165.0,
                step=5.0,
                key="comb_traded_value"
            ) * 1_000_000
            
            comb_commission_rate = st.number_input(
                "Commission Rate (bps)",
                min_value=1.0,
                max_value=50.0,
                value=round(baseline['commission_rate_bps'], 1),
                step=0.5,
                key="comb_commission_rate"
            )
            
            st.markdown("#### Investment Income Inputs")
            
            comb_portfolio = st.number_input(
                "Investment Portfolio (AED Billions)",
                min_value=1.0,
                max_value=20.0,
                value=round(baseline['total_investment_portfolio']/1_000_000, 2),
                step=0.1,
                key="comb_portfolio"
            ) * 1_000_000
            
            comb_interest_rate = st.number_input(
                "Interest Rate (%)",
                min_value=0.0,
                max_value=15.0,
                value=5.0,
                step=0.25,
                key="comb_interest_rate"
            )
        
        with col_right:
            st.markdown("#### Results")
            
            # Calculate
            comb_commission = calculate_trading_commission_scenario(comb_traded_value, comb_commission_rate)
            comb_investment_income = calculate_investment_income_scenario(comb_portfolio, comb_interest_rate)
            comb_total = comb_commission + comb_investment_income
            
            # Baseline comparison
            baseline_commission = baseline['trading_commission_annual']
            baseline_investment = baseline['investment_income_annual']
            baseline_total = baseline_commission + baseline_investment
            
            # Changes
            commission_delta = comb_commission - baseline_commission
            investment_delta = comb_investment_income - baseline_investment
            total_delta = comb_total - baseline_total
            
            # Display
            results_data = {
                'Revenue Stream': ['Trading Commission', 'Investment Income', 'TOTAL'],
                'Baseline (Annual)': [
                    format_aed_millions(baseline_commission),
                    format_aed_millions(baseline_investment),
                    format_aed_millions(baseline_total)
                ],
                'Scenario': [
                    format_aed_millions(comb_commission),
                    format_aed_millions(comb_investment_income),
                    format_aed_millions(comb_total)
                ],
                'Change': [
                    format_aed_millions(commission_delta),
                    format_aed_millions(investment_delta),
                    format_aed_millions(total_delta)
                ]
            }
            
            st.dataframe(pd.DataFrame(results_data), hide_index=True, use_container_width=True)
            
            # Summary metrics
            st.markdown("---")
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Trading Commission", format_aed_millions(comb_commission), 
                         f"{commission_delta/1000:+,.0f}M vs baseline")
            with m2:
                st.metric("Investment Income", format_aed_millions(comb_investment_income),
                         f"{investment_delta/1000:+,.0f}M vs baseline")
            with m3:
                st.metric("Combined Impact", format_aed_millions(total_delta),
                         f"{(total_delta/baseline_total)*100:+.1f}% change")
            
            # Waterfall chart
            fig4 = go.Figure(go.Waterfall(
                name="Impact",
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["Baseline Total", "Commission Δ", "Investment Δ", "Scenario Total"],
                y=[baseline_total/1000, commission_delta/1000, investment_delta/1000, comb_total/1000],
                text=[f"AED {baseline_total/1000:,.0f}M", f"{commission_delta/1000:+,.0f}M", 
                      f"{investment_delta/1000:+,.0f}M", f"AED {comb_total/1000:,.0f}M"],
                textposition="outside",
                connector={"line": {"color": "#0066CC", "width": 2}},
                decreasing={"marker": {"color": "#DC3545"}},
                increasing={"marker": {"color": "#28A745"}},
                totals={"marker": {"color": "#0066CC"}}
            ))
            
            fig4.update_layout(
                title="Revenue Bridge: Baseline → Scenario",
                yaxis_title="AED Millions",
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color='#1A1A1A'),
                showlegend=False
            )
            fig4.update_xaxes(showgrid=False)
            fig4.update_yaxes(gridcolor='#E0E0E0')
            
            st.plotly_chart(fig4, use_container_width=True)
    
    # -------------------------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------------------------
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption("**Data Source:** DFM Q3 2025 Condensed Interim Consolidated Financial Statements")
    with col2:
        st.caption("**Disclaimer:** For internal analysis only. Not investment advice.")


if __name__ == "__main__":
    main()
