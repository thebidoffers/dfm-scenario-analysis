# DFM Scenario Analysis Tool v3.0

**Dubai Financial Market - Earnings Sensitivity Analysis**

A dynamic web application that extracts financial data from uploaded documents and performs scenario analysis on DFM's key revenue streams.

---

## 🎯 Key Features

### 📁 Dynamic File Upload
- **Financial Statement (PDF)**: Upload DFM quarterly/annual financial statements
- **Market Bulletin (Excel)**: Upload DFM Yearly Bulletin with trading data

The app automatically extracts:
- Trading Commission Income
- Investment Income  
- Investment Portfolio Size (Deposits + Sukuks)
- Total Traded Value
- Implied Commission Rate

### 📊 Scenario Analysis
1. **Commission Fee Scenarios** - Model fee rate reductions
2. **Traded Value Scenarios** - ADTV × 252 days or total annual value
3. **Interest Rate Scenarios** - Simple portfolio × rate calculation
4. **Combined Scenarios** - Multiple factors together

---

## 🚀 Quick Start

### Deploy on Streamlit Cloud

1. Push this code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository and deploy

### Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Supported File Formats

### Financial Statement PDF
- DFM Condensed Interim Consolidated Financial Statements
- Quarterly (Q1, Q2, Q3) or Annual reports
- Must contain income statement and balance sheet

### Market Bulletin Excel
- DFM Yearly Bulletin (.xlsx)
- Must contain "Trade Value" column
- Should have "Market Grand Total" or similar summary row

---

## 📁 Project Files

```
dfm-scenario-analysis/
├── app.py                 # Main application
├── requirements.txt       # Dependencies  
├── README.md             # Documentation
└── .streamlit/
    └── config.toml       # Theme config
```

---

## ⚙️ Manual Override

If file parsing doesn't capture all values correctly, enable "Manual Overrides" in the sidebar to enter values directly.

---

## 📦 Dependencies

- `streamlit` - Web framework
- `pandas` - Data processing
- `plotly` - Interactive charts
- `pdfplumber` - PDF text extraction
- `openpyxl` - Excel file reading

---

**Built for DFM Finance Team**
