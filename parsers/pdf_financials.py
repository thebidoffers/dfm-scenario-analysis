from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pdfplumber

from .common import compute_portfolio, label_matches, normalize_label, parse_number


INCOME_LABELS = {
    "trading_commission": [
        "trading commission fees",
        "trading commission fee",
        "trading commission",
    ],
    "investment_income": [
        "investment income",
    ],
    "dividend_income": [
        "dividend income",
    ],
    "finance_income": [
        "finance income",
    ],
}

BALANCE_LABELS = {
    "investment_deposits": [
        "investment deposits",
        "deposits at banks",
        "time deposits",
    ],
    "investments_amortised_cost": [
        "investments at amortised cost",
        "financial assets at amortised cost",
    ],
    "fvtoci": [
        "fair value through other comprehensive income",
        "financial assets measured at fair value through other comprehensive income",
        "fair value through other comprehensive income fvtoci",
        "fvtoci",
        "fvto ci",
        "fvoci",
    ],
    "fvtpl": [
        "fair value through profit or loss",
        "fvtpl",
    ],
}

SECTION_HINTS = {
    "income": [
        "statement of profit or loss",
        "statement of comprehensive income",
        "income statement",
    ],
    "balance": [
        "statement of financial position",
        "balance sheet",
    ],
    "equity": [
        "statement of changes in equity",
    ],
    "cashflow": [
        "statement of cash flows",
    ],
}


@dataclass
class Candidate:
    metric: str
    value: float
    page: int
    snippet: str
    method: str
    score: int


def _page_section(text: str) -> Optional[str]:
    lowered = text.lower()
    for section, hints in SECTION_HINTS.items():
        if any(hint in lowered for hint in hints):
            return section
    return None


def _detect_year_columns(headers: List[str]) -> Optional[int]:
    years = []
    for idx, header in enumerate(headers):
        match = re.search(r"20\d{2}", str(header))
        if match:
            years.append((int(match.group(0)), idx))
    if not years:
        return None
    years.sort(reverse=True)
    return years[0][1]


def _detect_year_order(text: str) -> Optional[Tuple[int, int]]:
    match = re.search(r"(20\d{2})\s+(20\d{2})", text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _choose_current_period_value(
    match: re.Match, year_order: Optional[Tuple[int, int]]
) -> Optional[str]:
    first = match.group(1)
    second = match.group(2)
    if second is None:
        return first
    first_val = parse_number(first)
    second_val = parse_number(second)
    if first_val is not None and second_val is not None:
        # Heuristic: skip note numbers like "20" when followed by a larger value.
        if abs(first_val) <= 50 and abs(second_val) > 50:
            return second
    if year_order and year_order[0] < year_order[1]:
        return second
    return first


def _extract_table_candidates(
    table: List[List[str]],
    page_number: int,
    section: Optional[str],
) -> List[Candidate]:
    candidates: List[Candidate] = []
    if not table:
        return candidates
    header_row = [str(cell or "").strip() for cell in table[0]]
    year_col = _detect_year_columns(header_row)

    for row in table[1:]:
        if not row:
            continue
        label_cell = next((cell for cell in row if cell not in (None, "")), "")
        label = str(label_cell).strip()
        if not label:
            continue
        numeric_values = []
        for idx, cell in enumerate(row[1:], start=1):
            value = parse_number(cell)
            if value is None:
                continue
            numeric_values.append((idx, value))
        if not numeric_values:
            continue
        if year_col is not None:
            value = next((val for idx, val in numeric_values if idx == year_col), None)
            if value is None:
                value = numeric_values[0][1]
        else:
            value = numeric_values[0][1]

        snippet = " | ".join(str(cell or "").strip() for cell in row if cell)
        for metric, labels in {**INCOME_LABELS, **BALANCE_LABELS}.items():
            if label_matches(label, labels):
                score = 1
                if metric in INCOME_LABELS and section == "income":
                    score += 1
                if metric in BALANCE_LABELS and section == "balance":
                    score += 1
                candidates.append(
                    Candidate(
                        metric=metric,
                        value=value,
                        page=page_number,
                        snippet=snippet,
                        method="table",
                        score=score,
                    )
                )
    return candidates


def _regex_candidates(
    text: str,
    page_number: int,
    section: Optional[str],
    year_order: Optional[Tuple[int, int]],
) -> List[Candidate]:
    candidates: List[Candidate] = []
    for metric, labels in {**INCOME_LABELS, **BALANCE_LABELS}.items():
        for label in labels:
            pattern = (
                rf"{re.escape(label)}\s*(?:\([^)]*\)\s*)?"
                rf"(?:\d+\s*\(?[a-z]\)?\s*)?(?:[\s:]+)"
                rf"(-?\(?[\d,]+\)?)(?:\s+(-?\(?[\d,]+\)?))?"
            )
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                raw = _choose_current_period_value(match, year_order)
                value = parse_number(raw)
                if value is None:
                    continue
                snippet = match.group(0)[:200]
                score = 1
                if metric in INCOME_LABELS and section == "income":
                    score += 1
                if metric in BALANCE_LABELS and section == "balance":
                    score += 1
                if metric in BALANCE_LABELS and section in {"equity", "cashflow"}:
                    score -= 1
                if metric == "fvtoci" and section in {"equity", "cashflow"}:
                    score -= 2
                candidates.append(
                    Candidate(
                        metric=metric,
                        value=value,
                        page=page_number,
                        snippet=snippet,
                        method="regex",
                        score=score,
                    )
                )
    return candidates


def _best_candidates(candidates: Iterable[Candidate]) -> Dict[str, Candidate]:
    best: Dict[str, Candidate] = {}
    for candidate in candidates:
        current = best.get(candidate.metric)
        if current is None or candidate.score > current.score:
            best[candidate.metric] = candidate
    return best


def parse_pdf_financials(file) -> Dict[str, object]:
    metrics: Dict[str, float] = {}
    audit: List[Dict[str, object]] = []
    items: List[str] = []
    candidates: List[Candidate] = []

    texts: List[str] = []
    with pdfplumber.open(file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            texts.append(text)
            section = _page_section(text)
            year_order = _detect_year_order(text)
            for table in page.extract_tables() or []:
                candidates.extend(_extract_table_candidates(table, page_number, section))
            candidates.extend(_regex_candidates(text, page_number, section, year_order))

    best = _best_candidates(candidates)

    for metric, candidate in best.items():
        metrics[metric] = candidate.value
        audit.append(
            {
                "metric_name": metric,
                "value": candidate.value,
                "method": candidate.method,
                "page": candidate.page,
                "snippet": candidate.snippet,
                "confidence": f"score={candidate.score}",
            }
        )

    text_all = " ".join(texts).lower()
    if "nine-month" in text_all:
        metrics["period_months"] = 9
    elif "six-month" in text_all:
        metrics["period_months"] = 6
    elif "year ended" in text_all:
        metrics["period_months"] = 12

    if "trading_commission" in metrics:
        items.append(f"Trading Comm: {metrics['trading_commission']:,.0f}")
    if "investment_income" in metrics:
        items.append(f"Inv Income: {metrics['investment_income']:,.0f}")
    if "investment_deposits" in metrics:
        items.append(f"Investment Deposits: {metrics['investment_deposits']:,.0f}")
    if "investments_amortised_cost" in metrics:
        items.append(
            f"Investments at Amortised Cost: {metrics['investments_amortised_cost']:,.0f}"
        )
    if "fvtoci" in metrics:
        items.append(f"FVTOCI: {metrics['fvtoci']:,.0f}")
    if "fvtpl" in metrics:
        items.append(f"FVTPL: {metrics['fvtpl']:,.0f}")

    return {"metrics": metrics, "audit": audit, "items": items}


def compute_portfolio_from_metrics(metrics: Dict[str, float]) -> Optional[float]:
    return compute_portfolio(
        [
            metrics.get("investment_deposits"),
            metrics.get("investments_amortised_cost"),
            metrics.get("fvtoci"),
            metrics.get("fvtpl"),
        ]
    )
