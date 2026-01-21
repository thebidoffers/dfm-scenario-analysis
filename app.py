"""
DFM Scenario Analysis Tool
Dubai Financial Market - Earnings Sensitivity Analysis
Dynamic file upload version

Author: DFM Finance Team
Version: 3.0.0
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import io

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
# CLEAN CSS STYLING
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
    
    .section-divider {
        border: none;
        height: 1px;
        background: #E0E0E0;
        margin: 1.5rem 0;
    }
    
    .info-box {
        background: var(--dfm-blue-light);
        border-left: 4px solid var(--dfm-blue);
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        color: var(--dfm-black);
    }
    
    .success-box {
        background: #E8F5E9;
        border-left: 4px solid var(--dfm-green);
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        color: var(--dfm-black);
    }
    
    .warning-box {
        background: #FFF3E0;
        border-left: 4px solid #FF9800;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        color: var(--dfm-black);
    }
    
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
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stMetricValue"] {
        color: var(--dfm-blue) !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# FILE PARSING FUNCTIONS
# ============================================================================

def parse_financial_statement_pdf(uploaded_file):
    """
    Parse DFM financial statement PDF to extract key figures.
    Uses pdfplumber for text extraction.
    """
    try:
        import pdfplumber
    except ImportError:
        st.error("pdfplumber library not available. Please install it.")
        return None
    
    data = {
        'trading_commission_fees': None,
        'investment_income': None,
        'investment_deposits': None,
        'investments_amortised_cost': None,
        'period_months': 9,  # Default to 9 months (Q3)
        'source': 'PDF Upload'
    }
    
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # Extract Trading Commission Fees (9-month figure)
            # Looking for pattern like "Trading commission fees 113,272 45,827 310,195 138,179"
            trading_match = re.search(
                r'Trading commission fees[\s\S]*?([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)',
                full_text, re.IGNORECASE
            )
            if trading_match:
                # The third number is typically the 9-month current year figure
                data['trading_commission_fees'] = float(trading_match.group(3).replace(',', ''))
            
            # Alternative pattern for trading commission
            if data['trading_commission_fees'] is None:
                alt_match = re.search(r'Trading commission fees[^\d]*([\d,]+)', full_text, re.IGNORECASE)
                if alt_match:
                    data['trading_commission_fees'] = float(alt_match.group(1).replace(',', ''))
            
            # Extract Investment Income
            investment_match = re.search(
                r'Investment income[\s\S]*?([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)',
                full_text, re.IGNORECASE
            )
            if investment_match:
                data['investment_income'] = float(investment_match.group(3).replace(',', ''))
            
            if data['investment_income'] is None:
                alt_match = re.search(r'Investment income[^\d]*([\d,]+)', full_text, re.IGNORECASE)
                if alt_match:
                    data['investment_income'] = float(alt_match.group(1).replace(',', ''))
            
            # Extract Investment Deposits from balance sheet
            deposits_match = re.search(
                r'Investment deposits[^\d]*([\d,]+)',
                full_text, re.IGNORECASE
            )
            if deposits_match:
                data['investment_deposits'] = float(deposits_match.group(1).replace(',', ''))
            
            # Extract Investments at amortised cost
            amortised_match = re.search(
                r'Investments at amortised cost[^\d]*([\d,]+)',
                full_text, re.IGNORECASE
            )
            if amortised_match:
                data['investments_amortised_cost'] = float(amortised_match.group(1).replace(',', ''))
            
            # Determine period (Q1=3months, Q2=6months, Q3=9months)
            if 'nine-month' in full_text.lower() or 'nine month' in full_text.lower():
                data['period_months'] = 9
            elif 'six-month' in full_text.lower() or 'six month' in full_text.lower():
                data['period_months'] = 6
            elif 'three-month' in full_text.lower() or 'three month' in full_text.lower():
                data['period_months'] = 3
            elif 'year ended' in full_text.lower():
                data['period_months'] = 12
                
    except Exception as e:
        st.error(f"Error parsing PDF: {str(e)}")
        return None
    
    return data


def parse_bulletin_excel(uploaded_file):
    """
    Parse DFM Yearly Bulletin Excel file to extract total traded value.
    """
    data = {
        'total_traded_value': None,
        'total_trades': None,
        'source': 'Excel Upload'
    }
    
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file, sheet_name=0, header=1)
        
        # Clean Trade Value column
        if 'Trade Value' in df.columns:
            df['Trade Value Clean'] = pd.to_numeric(
                df['Trade Value'].astype(str).str.replace(',', ''), 
                errors='coerce'
            )
            
            # Look for Market Grand Total or Market Trades Total row
            market_total_row = df[
                df['Symbol-Security Name'].str.contains('Market Grand Total|Market Trades Total', 
                                                        na=False, case=False)
            ]
            
            if not market_total_row.empty:
                data['total_traded_value'] = market_total_row['Trade Value Clean'].values[0]
            else:
                # If no total row, look for "Shares Grand Total"
                shares_total = df[
                    df['Symbol-Security Name'].str.contains('Shares Grand Total', na=False, case=False)
                ]
                if not shares_total.empty:
                    data['total_traded_value'] = shares_total['Trade Value Clean'].values[0]
            
            # Get number of trades if available
            if 'No. of Trades' in df.columns:
                trades_col = pd.to_numeric(
                    df['No. of Trades'].astype(str).str.replace(',', ''),
                    errors='coerce'
                )
                if not market_total_row.empty:
                    data['total_trades'] = market_total_row['No. of Trades'].values[0]
                    if isinstance(data['total_trades'], str):
                        data['total_trades'] = float(data['total_trades'].replace(',', ''))
                        
    except Exception as e:
        st.error(f"Error parsing Excel: {str(e)}")
        return None
    
    return data


def format_aed_millions(value_thousands):
    """Format AED thousands to millions with M suffix"""
    if value_thousands is None:
        return "N/A"
    return f"AED {value_thousands/1000:,.1f}M"


def format_aed_billions(value_thousands):
    """Format AED thousands to billions with B suffix"""
    if value_thousands is None:
        return "N/A"
    return f"AED {value_thousands/1000000:,.1f}B"


def calculate_trading_commission_scenario(traded_value, commission_rate_bps):
    """Calculate trading commission based on traded value and rate"""
    if traded_value is None or commission_rate_bps is None:
        return 0
    return traded_value * (commission_rate_bps / 10000)


def calculate_investment_income_scenario(portfolio_size, interest_rate_pct):
    """Calculate investment income based on portfolio and rate"""
    if portfolio_size is None or interest_rate_pct is None:
        return 0
    return portfolio_size * (interest_rate_pct / 100)


# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------
    st.markdown('<p class="main-header">📊 DFM Scenario Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Dubai Financial Market | Earnings Sensitivity Tool</p>', unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # SIDEBAR - FILE UPLOADS
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("## 📁 Data Sources")
        
        st.markdown("### Financial Statement")
        st.caption("Upload DFM quarterly/annual financial statement (PDF)")
        fs_file = st.file_uploader(
            "Choose PDF file",
            type=['pdf'],
            key="fs_upload",
            help="Upload the DFM condensed interim or annual financial statement PDF"
        )
        
        st.markdown("### Market Trading Data")
        st.caption("Upload DFM Yearly Bulletin (Excel)")
        bulletin_file = st.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            key="bulletin_upload",
            help="Upload the DFM Yearly Bulletin Excel file with trading data"
        )
        
        st.markdown("---")
        
        # Manual override section
        st.markdown("### ⚙️ Manual Overrides")
        st.caption("Override extracted values if needed")
        
        use_manual = st.checkbox("Enable manual data entry", value=False)
    
    # -------------------------------------------------------------------------
    # PROCESS UPLOADED FILES
    # -------------------------------------------------------------------------
    fs_data = None
    bulletin_data = None
    
    if fs_file is not None:
        fs_data = parse_financial_statement_pdf(fs_file)
    
    if bulletin_file is not None:
        bulletin_data = parse_bulletin_excel(bulletin_file)
    
    # -------------------------------------------------------------------------
    # INITIALIZE DATA (from uploads or defaults)
    # -------------------------------------------------------------------------
    # Default values (will be overridden by uploads)
    defaults = {
        'trading_commission': 310_195,  # AED '000 (9 months)
        'investment_income': 165_348,   # AED '000 (9 months)
        'investment_deposits': 4_134_622,  # AED '000
        'investments_amortised_cost': 367_717,  # AED '000
        'total_traded_value': 165_000_000,  # AED '000 (165 billion)
        'period_months': 9,
        'trading_days': 252,
        'avg_interest_rate': 5.0
    }
    
    # Update with parsed data
    if fs_data:
        if fs_data.get('trading_commission_fees'):
            defaults['trading_commission'] = fs_data['trading_commission_fees']
        if fs_data.get('investment_income'):
            defaults['investment_income'] = fs_data['investment_income']
        if fs_data.get('investment_deposits'):
            defaults['investment_deposits'] = fs_data['investment_deposits']
        if fs_data.get('investments_amortised_cost'):
            defaults['investments_amortised_cost'] = fs_data['investments_amortised_cost']
        if fs_data.get('period_months'):
            defaults['period_months'] = fs_data['period_months']
    
    if bulletin_data:
        if bulletin_data.get('total_traded_value'):
            defaults['total_traded_value'] = bulletin_data['total_traded_value']
    
    # Calculate derived values
    defaults['total_investment_portfolio'] = defaults['investment_deposits'] + defaults['investments_amortised_cost']
    defaults['adtv'] = defaults['total_traded_value'] / defaults['trading_days']
    defaults['trading_commission_annual'] = defaults['trading_commission'] * (12 / defaults['period_months'])
    defaults['investment_income_annual'] = defaults['investment_income'] * (12 / defaults['period_months'])
    defaults['commission_rate_bps'] = (defaults['trading_commission_annual'] / defaults['total_traded_value']) * 10000
    
    # -------------------------------------------------------------------------
    # MANUAL OVERRIDE INPUTS (in sidebar)
    # -------------------------------------------------------------------------
    if use_manual:
        with st.sidebar:
            defaults['trading_commission'] = st.number_input(
                "Trading Commission (AED '000)",
                value=float(defaults['trading_commission']),
                step=1000.0,
                key="manual_trading_comm"
            )
            defaults['investment_income'] = st.number_input(
                "Investment Income (AED '000)",
                value=float(defaults['investment_income']),
                step=1000.0,
                key="manual_inv_income"
            )
            defaults['total_investment_portfolio'] = st.number_input(
                "Investment Portfolio (AED '000)",
                value=float(defaults['total_investment_portfolio']),
                step=10000.0,
                key="manual_portfolio"
            )
            defaults['total_traded_value'] = st.number_input(
                "Total Traded Value (AED '000)",
                value=float(defaults['total_traded_value']),
                step=1000000.0,
                key="manual_traded_value"
            )
            defaults['period_months'] = st.selectbox(
                "Reporting Period",
                options=[3, 6, 9, 12],
                index=[3, 6, 9, 12].index(defaults['period_months']),
                format_func=lambda x: f"{x} months",
                key="manual_period"
            )
            
            # Recalculate derived values
            defaults['adtv'] = defaults['total_traded_value'] / defaults['trading_days']
            defaults['trading_commission_annual'] = defaults['trading_commission'] * (12 / defaults['period_months'])
            defaults['investment_income_annual'] = defaults['investment_income'] * (12 / defaults['period_months'])
            defaults['commission_rate_bps'] = (defaults['trading_commission_annual'] / defaults['total_traded_value']) * 10000
    
    # -------------------------------------------------------------------------
    # DATA STATUS DISPLAY
    # -------------------------------------------------------------------------
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # Show data source status
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        if fs_file:
            st.markdown(f"""
            <div class="success-box">
                <strong>✅ Financial Statement Loaded</strong><br>
                Period: {defaults['period_months']} months<br>
                Trading Commission: {format_aed_millions(defaults['trading_commission'])}<br>
                Investment Income: {format_aed_millions(defaults['investment_income'])}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="warning-box">
                <strong>⚠️ No Financial Statement</strong><br>
                Using default Q3 2025 values.<br>
                Upload a PDF for latest data.
            </div>
            """, unsafe_allow_html=True)
    
    with col_status2:
        if bulletin_file:
            st.markdown(f"""
            <div class="success-box">
                <strong>✅ Market Bulletin Loaded</strong><br>
                Total Traded Value: {format_aed_billions(defaults['total_traded_value'])}<br>
                ADTV (252 days): {format_aed_millions(defaults['adtv'])}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="warning-box">
                <strong>⚠️ No Market Bulletin</strong><br>
                Using default 2025 values.<br>
                Upload Excel for latest data.
            </div>
            """, unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # KEY METRICS DISPLAY
    # -------------------------------------------------------------------------
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📋 Extracted Baseline Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="metric-label">Trading Commission ({defaults['period_months']}M)</div>
            <div class="metric-value-blue">{format_aed_millions(defaults['trading_commission'])}</div>
            <div style="color: #666; font-size: 0.75rem;">Annualized: {format_aed_millions(defaults['trading_commission_annual'])}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="metric-label">Average Daily Traded Value</div>
            <div class="metric-value-blue">{format_aed_millions(defaults['adtv'])}</div>
            <div style="color: #666; font-size: 0.75rem;">Total: {format_aed_billions(defaults['total_traded_value'])}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="metric-label">Investment Portfolio Size</div>
            <div class="metric-value-blue">{format_aed_billions(defaults['total_investment_portfolio'])}</div>
            <div style="color: #666; font-size: 0.75rem;">Deposits + Sukuks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card-highlight">
            <div class="metric-label">Investment Income ({defaults['period_months']}M)</div>
            <div class="metric-value-blue">{format_aed_millions(defaults['investment_income'])}</div>
            <div style="color: #666; font-size: 0.75rem;">Annualized: {format_aed_millions(defaults['investment_income_annual'])}</div>
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
            
            use_custom_traded_value_t1 = st.checkbox("Override traded value", key="t1_override", value=False)
            if use_custom_traded_value_t1:
                custom_traded_value_t1 = st.number_input(
                    "Total Annual Traded Value (AED Billions)",
                    min_value=50.0,
                    max_value=500.0,
                    value=defaults['total_traded_value']/1_000_000,
                    step=5.0,
                    key="t1_traded_value"
                ) * 1_000_000
            else:
                custom_traded_value_t1 = defaults['total_traded_value']
            
            st.markdown("---")
            
            current_rate = st.number_input(
                "Current Commission Rate (bps)",
                min_value=1.0,
                max_value=50.0,
                value=round(defaults['commission_rate_bps'], 1),
                step=0.5,
                help=f"Calculated from data: ~{defaults['commission_rate_bps']:.1f} bps"
            )
            
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
            
            current_commission = calculate_trading_commission_scenario(custom_traded_value_t1, current_rate)
            new_commission = calculate_trading_commission_scenario(custom_traded_value_t1, new_rate)
            commission_change = new_commission - current_commission
            pct_change = (commission_change / current_commission * 100) if current_commission > 0 else 0
            
            res_col1, res_col2, res_col3 = st.columns(3)
            
            with res_col1:
                st.metric("Current Commission Income", format_aed_millions(current_commission))
            
            with res_col2:
                st.metric("New Commission Income", format_aed_millions(new_commission), 
                         delta=f"{rate_change:+.1f} bps rate change")
            
            with res_col3:
                delta_color = "normal" if commission_change >= 0 else "inverse"
                st.metric("Annual Impact", format_aed_millions(commission_change),
                         delta=f"{pct_change:+.1f}%", delta_color=delta_color)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Current', x=['Commission Income'], y=[current_commission/1000],
                                marker_color='#0066CC', text=[f'AED {current_commission/1000:,.0f}M'],
                                textposition='outside', width=0.3))
            fig.add_trace(go.Bar(name='Scenario', x=['Commission Income'], y=[new_commission/1000],
                                marker_color='#66B2FF', text=[f'AED {new_commission/1000:,.0f}M'],
                                textposition='outside', width=0.3))
            fig.update_layout(title='Trading Commission: Current vs Scenario', yaxis_title='AED Millions',
                            barmode='group', height=350, plot_bgcolor='white', paper_bgcolor='white',
                            font=dict(color='#1A1A1A'),
                            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
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
            
            input_method = st.radio("Input Method",
                                   ["Daily Traded Value × 252 days", "Total Annual Traded Value"],
                                   key="t2_method")
            
            if input_method == "Daily Traded Value × 252 days":
                current_adtv = st.number_input("Current ADTV (AED Millions)",
                                              min_value=100.0, max_value=5000.0,
                                              value=round(defaults['adtv']/1000, 0),
                                              step=50.0, key="t2_current_adtv")
                new_adtv = st.number_input("New ADTV (AED Millions)",
                                          min_value=100.0, max_value=5000.0,
                                          value=round(defaults['adtv']/1000 * 0.75, 0),
                                          step=50.0, key="t2_new_adtv")
                current_annual = current_adtv * 1000 * 252
                new_annual = new_adtv * 1000 * 252
            else:
                current_annual_input = st.number_input("Current Annual Traded Value (AED Billions)",
                                                       min_value=50.0, max_value=500.0,
                                                       value=defaults['total_traded_value']/1_000_000,
                                                       step=5.0, key="t2_current_annual")
                new_annual_input = st.number_input("New Annual Traded Value (AED Billions)",
                                                   min_value=50.0, max_value=500.0,
                                                   value=defaults['total_traded_value']/1_000_000 * 0.75,
                                                   step=5.0, key="t2_new_annual")
                current_annual = current_annual_input * 1_000_000
                new_annual = new_annual_input * 1_000_000
            
            st.markdown("---")
            commission_rate_t2 = st.number_input("Commission Rate (bps)",
                                                min_value=1.0, max_value=50.0,
                                                value=round(defaults['commission_rate_bps'], 1),
                                                step=0.5, key="t2_rate")
        
        with col_result:
            st.markdown("#### Impact Analysis")
            
            current_commission_t2 = calculate_trading_commission_scenario(current_annual, commission_rate_t2)
            new_commission_t2 = calculate_trading_commission_scenario(new_annual, commission_rate_t2)
            commission_change_t2 = new_commission_t2 - current_commission_t2
            traded_value_change_pct = ((new_annual - current_annual) / current_annual * 100) if current_annual > 0 else 0
            commission_change_pct_t2 = (commission_change_t2 / current_commission_t2 * 100) if current_commission_t2 > 0 else 0
            
            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                st.metric("Current Traded Value", format_aed_billions(current_annual))
            with res_col2:
                st.metric("New Traded Value", format_aed_billions(new_annual),
                         delta=f"{traded_value_change_pct:+.1f}%")
            with res_col3:
                delta_color = "normal" if commission_change_t2 >= 0 else "inverse"
                st.metric("Commission Impact", format_aed_millions(commission_change_t2),
                         delta=f"{commission_change_pct_t2:+.1f}%", delta_color=delta_color)
            
            comparison_data = {
                'Metric': ['Annual Traded Value', 'ADTV (252 days)', 'Commission Income'],
                'Current': [format_aed_billions(current_annual), format_aed_millions(current_annual/252),
                           format_aed_millions(current_commission_t2)],
                'Scenario': [format_aed_billions(new_annual), format_aed_millions(new_annual/252),
                            format_aed_millions(new_commission_t2)],
                'Change': [f"{traded_value_change_pct:+.1f}%", f"{traded_value_change_pct:+.1f}%",
                          f"{format_aed_millions(commission_change_t2)} ({commission_change_pct_t2:+.1f}%)"]
            }
            st.dataframe(pd.DataFrame(comparison_data), hide_index=True, use_container_width=True)
            
            fig2 = go.Figure()
            categories = ['Traded Value (B)', 'Commission (M)']
            current_vals = [current_annual/1_000_000, current_commission_t2/1000]
            new_vals = [new_annual/1_000_000, new_commission_t2/1000]
            fig2.add_trace(go.Bar(name='Current', x=categories, y=current_vals, marker_color='#0066CC',
                                 text=[f'{v:,.0f}' for v in current_vals], textposition='outside'))
            fig2.add_trace(go.Bar(name='Scenario', x=categories, y=new_vals, marker_color='#66B2FF',
                                 text=[f'{v:,.0f}' for v in new_vals], textposition='outside'))
            fig2.update_layout(title='Traded Value & Commission Impact', barmode='group', height=350,
                              plot_bgcolor='white', paper_bgcolor='white', font=dict(color='#1A1A1A'),
                              legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
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
            
            portfolio_size = st.number_input("Investment Portfolio Size (AED Billions)",
                                            min_value=1.0, max_value=20.0,
                                            value=round(defaults['total_investment_portfolio']/1_000_000, 2),
                                            step=0.1, help=f"From data: AED {defaults['total_investment_portfolio']/1_000_000:.1f}B"
                                            ) * 1_000_000
            
            st.markdown("---")
            
            current_interest_rate = st.number_input("Current Interest Rate (%)",
                                                   min_value=0.0, max_value=15.0,
                                                   value=5.0, step=0.25)
            
            rate_change_option = st.selectbox("Interest Rate Change",
                ["+50 bps", "+25 bps", "No change", "-25 bps", "-50 bps", "-100 bps", "-150 bps", "Custom"],
                index=4, key="t3_rate_change")
            
            if rate_change_option == "Custom":
                rate_change_bps = st.number_input("Custom Rate Change (bps)",
                                                 min_value=-500, max_value=500, value=-100, step=25)
            else:
                rate_map = {"+50 bps": 50, "+25 bps": 25, "No change": 0,
                           "-25 bps": -25, "-50 bps": -50, "-100 bps": -100, "-150 bps": -150}
                rate_change_bps = rate_map[rate_change_option]
            
            new_interest_rate = max(0, current_interest_rate + (rate_change_bps / 100))
            st.info(f"New Interest Rate: **{new_interest_rate:.2f}%**")
        
        with col_result:
            st.markdown("#### Impact Analysis")
            
            current_investment_income = calculate_investment_income_scenario(portfolio_size, current_interest_rate)
            new_investment_income = calculate_investment_income_scenario(portfolio_size, new_interest_rate)
            income_change = new_investment_income - current_investment_income
            income_change_pct = (income_change / current_investment_income * 100) if current_investment_income > 0 else 0
            
            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                st.metric("Current Investment Income", format_aed_millions(current_investment_income),
                         delta=f"@ {current_interest_rate:.2f}%")
            with res_col2:
                st.metric("New Investment Income", format_aed_millions(new_investment_income),
                         delta=f"@ {new_interest_rate:.2f}%")
            with res_col3:
                delta_color = "normal" if income_change >= 0 else "inverse"
                st.metric("Annual Impact", format_aed_millions(income_change),
                         delta=f"{income_change_pct:+.1f}%", delta_color=delta_color)
            
            st.markdown(f"""
            <div class="info-box">
                <strong>Calculation:</strong><br>
                Portfolio: {format_aed_billions(portfolio_size)} × Rate Change: {rate_change_bps:+d} bps<br>
                = <strong>{format_aed_millions(income_change)}</strong> annual impact
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### Rate Sensitivity Table")
            rate_scenarios = [100, 50, 25, 0, -25, -50, -100, -150, -200]
            sensitivity_data = []
            for rate_chg in rate_scenarios:
                new_rate = max(0, current_interest_rate + (rate_chg / 100))
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
            comb_traded_value = st.number_input("Annual Traded Value (AED Billions)",
                                               min_value=50.0, max_value=500.0,
                                               value=defaults['total_traded_value']/1_000_000,
                                               step=5.0, key="comb_traded_value") * 1_000_000
            comb_commission_rate = st.number_input("Commission Rate (bps)",
                                                  min_value=1.0, max_value=50.0,
                                                  value=round(defaults['commission_rate_bps'], 1),
                                                  step=0.5, key="comb_commission_rate")
            
            st.markdown("#### Investment Income Inputs")
            comb_portfolio = st.number_input("Investment Portfolio (AED Billions)",
                                            min_value=1.0, max_value=20.0,
                                            value=round(defaults['total_investment_portfolio']/1_000_000, 2),
                                            step=0.1, key="comb_portfolio") * 1_000_000
            comb_interest_rate = st.number_input("Interest Rate (%)",
                                                min_value=0.0, max_value=15.0,
                                                value=5.0, step=0.25, key="comb_interest_rate")
        
        with col_right:
            st.markdown("#### Results")
            
            comb_commission = calculate_trading_commission_scenario(comb_traded_value, comb_commission_rate)
            comb_investment_income = calculate_investment_income_scenario(comb_portfolio, comb_interest_rate)
            comb_total = comb_commission + comb_investment_income
            
            baseline_commission = defaults['trading_commission_annual']
            baseline_investment = defaults['investment_income_annual']
            baseline_total = baseline_commission + baseline_investment
            
            commission_delta = comb_commission - baseline_commission
            investment_delta = comb_investment_income - baseline_investment
            total_delta = comb_total - baseline_total
            
            results_data = {
                'Revenue Stream': ['Trading Commission', 'Investment Income', 'TOTAL'],
                'Baseline (Annual)': [format_aed_millions(baseline_commission),
                                     format_aed_millions(baseline_investment),
                                     format_aed_millions(baseline_total)],
                'Scenario': [format_aed_millions(comb_commission),
                            format_aed_millions(comb_investment_income),
                            format_aed_millions(comb_total)],
                'Change': [format_aed_millions(commission_delta),
                          format_aed_millions(investment_delta),
                          format_aed_millions(total_delta)]
            }
            st.dataframe(pd.DataFrame(results_data), hide_index=True, use_container_width=True)
            
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
                         f"{(total_delta/baseline_total)*100:+.1f}% change" if baseline_total > 0 else "N/A")
            
            fig4 = go.Figure(go.Waterfall(
                name="Impact", orientation="v",
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
            fig4.update_layout(title="Revenue Bridge: Baseline → Scenario", yaxis_title="AED Millions",
                              height=400, plot_bgcolor='white', paper_bgcolor='white',
                              font=dict(color='#1A1A1A'), showlegend=False)
            fig4.update_xaxes(showgrid=False)
            fig4.update_yaxes(gridcolor='#E0E0E0')
            st.plotly_chart(fig4, use_container_width=True)
    
    # -------------------------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------------------------
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.caption("**Data Source:** Upload financial statements and market bulletins for latest data")
    with col2:
        st.caption("**Disclaimer:** For internal analysis only. Not investment advice.")


if __name__ == "__main__":
    main()
