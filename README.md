# DFM Scenario Analysis Tool

**Dubai Financial Market - Earnings Sensitivity Analysis**

A professional web application for analyzing the impact of various market scenarios on DFM's financial performance. Built with Streamlit and based on Q3 2025 financial statements.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-Internal-yellow.svg)

---

## 🎯 Overview

This tool enables DFM's finance team to model and analyze the financial impact of:

- **Trading Commission Changes**: What happens if commission rates drop by 5-15 basis points?
- **ADTV (Average Daily Traded Value) Changes**: Impact of 10-50% drops or increases in trading volume
- **Interest Rate Movements**: Effects of -25bp, -50bp, or -100bp rate cuts on investment income

## 📊 Data Foundation

Based on:
- **DFM Q3 2025 Condensed Interim Consolidated Financial Statements** (9 months ended 30 Sep 2025)
- **Full Year 2025 Traded Value**: AED 165 billion (from Yearly Bulletin)
- All figures are annualized for comparability

### Key Baseline Metrics (Annualized)

| Metric | Value |
|--------|-------|
| Trading Commission Fees | AED 413.6M |
| Investment Income | AED 220.5M |
| Total Income | AED 801.2M |
| Net Profit | AED 584.6M |
| Interest-Earning Assets | AED 4.5B |
| Commission Rate | ~25 bps |

## 🚀 Quick Start

### Option 1: Deploy on Streamlit Cloud (Recommended)

1. **Fork or clone this repository to your GitHub account**

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Click "New app" and connect your GitHub repository**

4. **Configure deployment:**
   - Repository: `your-username/dfm-scenario-analysis`
   - Branch: `main`
   - Main file path: `app.py`

5. **Click "Deploy"** - Your app will be live in minutes!

### Option 2: Run Locally

```bash
# Clone the repository
git clone https://github.com/your-username/dfm-scenario-analysis.git
cd dfm-scenario-analysis

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
dfm-scenario-analysis/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .streamlit/
│   └── config.toml       # Streamlit configuration (optional)
└── data/                 # Data files (optional)
    └── baseline.json     # Baseline financial data
```

## 🛠️ Features

### 1. Interactive Scenario Controls
- **Commission Rate Slider**: Adjust by -15 to +10 basis points
- **ADTV Change Slider**: Model -50% to +50% volume changes
- **Interest Rate Dropdown**: Select from +25bp to -100bp scenarios

### 2. Quick Scenario Presets
- **Bear Case**: -10bp commission, -30% ADTV, -100bp rates
- **Bull Case**: No commission change, +25% ADTV, no rate change
- **Reset**: Return to baseline assumptions

### 3. Visualizations
- **Income Breakdown Chart**: Side-by-side comparison of revenue components
- **Waterfall Analysis**: Bridge from baseline to scenario net profit
- **Sensitivity Heatmap**: Net profit across multiple scenario combinations
- **Interest Rate Sensitivity Table**: Detailed rate impact analysis

### 4. Detailed P&L
- Full pro forma income statement
- Line-by-line baseline vs scenario comparison
- Variance analysis

## 📈 Model Assumptions

| Component | Assumption |
|-----------|------------|
| Trading Commission | Scales with: Traded Value × Commission Rate |
| Clearing & Settlement | 100% proportional to traded value |
| Brokerage Fees | 50% fixed, 50% variable with volume |
| Other Fees | 70% fixed, 30% variable with volume |
| Investment Income | Linear scaling with interest rates |
| Operating Expenses | Treated as fixed costs |
| Tax Rate | 8.49% effective (from Q3 2025 actuals) |

## ⚙️ Configuration

### Streamlit Cloud Secrets (Optional)

If you want to add authentication or API keys, create a `.streamlit/secrets.toml` file:

```toml
[credentials]
password = "your-secure-password"
```

### Custom Theme

The app includes custom CSS styling. To modify the theme, edit the CSS in the `st.markdown()` section at the top of `app.py`.

## 🔒 Security Notes

- This tool is designed for **internal use only**
- No sensitive data is transmitted externally
- All calculations are performed client-side
- Consider adding authentication for production deployment

## 📝 Changelog

### v1.0.0 (January 2026)
- Initial release
- Based on Q3 2025 financial statements
- Three scenario dimensions: commission, ADTV, interest rates
- Four analysis tabs: Income Breakdown, Waterfall, Sensitivity Matrix, Detailed P&L

## 🤝 Contributing

For feature requests or bug reports, please contact the DFM Finance team.

## 📄 License

Internal use only. All rights reserved by Dubai Financial Market.

---

**Built with ❤️ for DFM**
