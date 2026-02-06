from __future__ import annotations

import pandas as pd

from .common import parse_number


def _clean_text(value) -> str:
    return str(value or "").strip().lower()


def parse_excel_bulletin(file) -> dict:
    metrics = {}
    audit = []
    items = []

    sheets = pd.read_excel(file, sheet_name=None, header=None)

    for sheet_name, df in sheets.items():
        if df.empty:
            continue
        normalized = df.fillna("").astype(str).applymap(_clean_text)

        trade_col_idx = None
        header_row_idx = None
        for row_idx in range(min(10, len(normalized))):
            row = normalized.iloc[row_idx]
            for col_idx, cell in row.items():
                if "trade value" in cell or "tradevalue" in cell:
                    trade_col_idx = col_idx
                    header_row_idx = row_idx
                    break
            if trade_col_idx is not None:
                break

        if trade_col_idx is None:
            for col_idx in normalized.columns:
                if normalized[col_idx].str.contains("trade value", case=False, na=False).any():
                    trade_col_idx = col_idx
                    break

        if trade_col_idx is None:
            continue

        row_mask = normalized.apply(
            lambda row: row.astype(str)
            .str.contains("market grand total", case=False, na=False)
            .any(),
            axis=1,
        )
        if not row_mask.any():
            continue

        row_idx = row_mask.idxmax()
        raw_value = df.at[row_idx, trade_col_idx]
        value = parse_number(raw_value)
        if value is None or value <= 0:
            continue

        metrics["total_traded_value"] = value / 1000
        items.append(f"Traded Value: {value:,.0f}")
        audit.append(
            {
                "metric_name": "total_traded_value",
                "value": metrics["total_traded_value"],
                "method": "excel",
                "page": None,
                "snippet": f"sheet={sheet_name}, row={row_idx}, col={trade_col_idx}",
                "confidence": f"header_row={header_row_idx}",
            }
        )
        break

    return {"metrics": metrics, "audit": audit, "items": items}
