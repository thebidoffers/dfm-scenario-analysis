# DFM Scenario Analysis Tool v2.0

**Dubai Financial Market - Earnings Sensitivity Analysis**

A clean, professional web application for analyzing the impact of various market scenarios on DFM's key revenue streams.

---

## 🎯 Overview

This tool enables DFM's finance team to model and analyze:

1. **Trading Commission Scenarios** - Impact of fee rate reductions
2. **Traded Value Scenarios** - Impact of ADTV or total volume changes
3. **Interest Rate Scenarios** - Impact of rate cuts on investment income
4. **Combined Scenarios** - Multiple factors changing together

## 📊 Baseline Data (from Q3 2025 Financials)

| Metric | Value | Source |
|--------|-------|--------|
| Trading Commission (9M) | AED 310.2M | Income Statement |
| Investment Income (9M) | AED 165.3M | Income Statement |
| Investment Portfolio | AED 4.5B | Balance Sheet (Deposits + Sukuks) |
| Total Traded Value 2025 | AED 165B | Yearly Bulletin |
| ADTV (252 days) | AED 655M | Calculated |
| Commission Rate | ~25 bps | Implied |
| Interest Rate | ~5.0% | Note 9 (4.4%-5.5% range) |

## 🚀 Quick Start

### Deploy on Streamlit Cloud

1. Push this code to your GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository and deploy

### Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📁 Files

```
dfm-scenario-analysis/
├── app.py                 # Main application
├── requirements.txt       # Dependencies
├── README.md             # This file
└── .streamlit/
    └── config.toml       # Theme configuration
```

## 🎨 Design

- Clean white background
- Blue (#0066CC) for highlights and key metrics
- Black text for readability
- Simple, professional charts

---

**Built for DFM Finance Team**
