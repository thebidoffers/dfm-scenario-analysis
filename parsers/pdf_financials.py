"""
DFM PDF Financial Statement Parser — Phase 1 Overhaul

Robust extraction of income lines, investment income breakdown,
and financial asset balances from DFM quarterly/annual consolidated
financial statements.

Key design principles:
 - Section scoping: INCOME_LABELS only matched on P&L pages,
   BALANCE_LABELS only on balance-sheet pages.
 - Correct year-column selection for 2-col (annual) and 4-col (interim).
 - Note-block extraction for Note 20 breakdown and Note 8 FVTOCI split.
 - Audit trail for every extracted metric.
 - Reconciliation validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import pdfplumber

from .common import compute_portfolio, parse_number

# ───────────────────────────────────────────────────────────
# 1) LABEL DICTIONARIES — keyed by metric name
# ───────────────────────────────────────────────────────────

INCOME_LABELS: Dict[str, List[str]] = {
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

BALANCE_LABELS: Dict[str, List[str]] = {
    "investment_deposits": [
        "investment deposits",
    ],
    "investments_amortised_cost": [
        "investments at amortised cost",
        "financial assets at amortised cost",
    ],
    "fvtoci": [
        "financial assets measured at fair value through other comprehensive income",
    ],
    "cash_and_equivalents": [
        "cash and cash equivalents",
    ],
}

# ───────────────────────────────────────────────────────────
# 2) SECTION DETECTION — classify each page
# ───────────────────────────────────────────────────────────

SECTION_PATTERNS = {
    "pl": [
        "consolidated statement of profit or loss",
        "consolidated statement of income",
        "condensed interim consolidated statement of income",
        "condensed interim consolidated statement of profit or loss",
    ],
    "bs": [
        "consolidated statement of financial position",
        "condensed interim consolidated statement of financial position",
    ],
    "oci": [
        "consolidated statement of comprehensive income",
        "condensed interim consolidated statement of comprehensive income",
    ],
    "cashflow": [
        "consolidated statement of cash flows",
        "condensed interim consolidated statement of cash flows",
    ],
}


def _classify_page(text: str) -> Optional[str]:
    """Return section type for a page, or None (= notes / other)."""
    lowered = text[:1500].lower()
    for section, patterns in SECTION_PATTERNS.items():
        for pat in patterns:
            if pat in lowered:
                return section
    return None


# ───────────────────────────────────────────────────────────
# 3) COLUMN LAYOUT DETECTION
# ───────────────────────────────────────────────────────────

_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_NUM_RE = re.compile(r"-?\(?\d[\d,]*\)?")


def _detect_column_count(page_text: str) -> int:
    """Detect number of year-columns on a statement page.

    DFM annual: 2 columns  (2025, 2024)
    DFM interim: 4 columns (Q current, Q prior, YTD current, YTD prior)
    Returns 2 or 4 (or 0 if indeterminate).
    """
    lines = page_text.split("\n")
    for line in lines[:15]:
        years = _YEAR_RE.findall(line)
        if len(years) >= 4:
            return 4
        if len(years) == 2:
            return 2
    return 0


def _detect_period_months(full_text: str) -> int:
    """Detect reporting period from document text."""
    lowered = full_text.lower()
    if "nine-month" in lowered or "nine- month" in lowered:
        return 9
    if "six-month" in lowered or "six- month" in lowered:
        return 6
    if "three-month" in lowered or "three- month" in lowered:
        return 3
    if "year ended" in lowered:
        return 12
    return 12


# ───────────────────────────────────────────────────────────
# 4) NUMBER EXTRACTION FROM A TEXT LINE
# ───────────────────────────────────────────────────────────


def _extract_line_numbers(line: str, label_end_pos: int = 0) -> List[float]:
    """Extract all numeric values from a line after the label.

    Filters out small 'note reference' numbers (1-99) that appear
    immediately after labels and before the real financial values.
    """
    tail = line[label_end_pos:]
    raw_matches = _NUM_RE.findall(tail)

    values = []
    for raw in raw_matches:
        v = parse_number(raw)
        if v is not None:
            values.append(v)

    if not values:
        return values

    # Filter note references: a small integer (< 100) as the first value,
    # followed by larger numbers, is likely a note ref.
    if (
        len(values) >= 2
        and abs(values[0]) < 100
        and any(abs(v) >= 100 for v in values[1:])
    ):
        values = values[1:]

    return values


def _pick_current_year_value(
    values: List[float],
    col_count: int,
    section: Optional[str],
) -> Optional[float]:
    """Select the current-year (or current cumulative period) value.

    - 2-column (annual): index 0 = current year
    - 4-column (interim P&L): index 2 = YTD current period
    - 2-column (interim BS): index 0 = current period
    - fallback: index 0
    """
    if not values:
        return None

    if col_count == 4 and section == "pl":
        # Interim P&L: Q-current, Q-prior, YTD-current, YTD-prior
        if len(values) >= 3:
            return values[2]
        return values[0]

    # Annual or balance sheet: first value is current year
    return values[0]


# ───────────────────────────────────────────────────────────
# 5) CANDIDATE MODEL & EXTRACTION
# ───────────────────────────────────────────────────────────

@dataclass
class Candidate:
    metric: str
    value: float
    page: int
    snippet: str
    method: str       # "table", "regex", "note_block"
    score: int = 0


def _normalise(text: str) -> str:
    """Lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower().strip())


def _label_matches(text: str, keywords: List[str]) -> Optional[str]:
    """Check if text starts with any keyword. Returns matched keyword or None."""
    norm = _normalise(text)
    for kw in keywords:
        kw_norm = _normalise(kw)
        if norm.startswith(kw_norm):
            return kw_norm
    return None


def _extract_regex_candidates(
    lines: List[str],
    page_number: int,
    section: Optional[str],
    col_count: int,
) -> List[Candidate]:
    """Line-by-line regex extraction, scoped to the correct section."""
    candidates: List[Candidate] = []

    # Choose label sets by section
    if section == "pl":
        label_sets = INCOME_LABELS
    elif section == "bs":
        label_sets = BALANCE_LABELS
    else:
        return candidates   # skip OCI, cashflow, notes for regex

    for metric, keywords in label_sets.items():
        for line in lines:
            matched_kw = _label_matches(line, keywords)
            if matched_kw is None:
                continue

            # Find where the keyword ends in the original line
            # Use case-insensitive search on the original line directly
            kw_pos = line.lower().find(matched_kw)
            if kw_pos >= 0:
                actual_end = kw_pos + len(matched_kw)
            else:
                # Fallback: build a flexible regex from the keyword
                kw_pattern = r"\s+".join(re.escape(w) for w in matched_kw.split())
                m = re.search(kw_pattern, line, re.IGNORECASE)
                if m:
                    actual_end = m.end()
                else:
                    continue

            values = _extract_line_numbers(line, actual_end)
            value = _pick_current_year_value(values, col_count, section)
            if value is None:
                continue

            # Score: base 1, +2 for correct primary statement
            score = 1
            if metric in INCOME_LABELS and section == "pl":
                score += 2
            elif metric in BALANCE_LABELS and section == "bs":
                score += 2

            candidates.append(Candidate(
                metric=metric,
                value=value,
                page=page_number,
                snippet=line.strip()[:200],
                method="regex",
                score=score,
            ))

    return candidates


def _extract_table_candidates(
    table: List[List[str]],
    page_number: int,
    section: Optional[str],
) -> List[Candidate]:
    """Extract candidates from pdfplumber table objects."""
    candidates: List[Candidate] = []
    if not table or len(table) < 2:
        return candidates

    if section == "pl":
        label_sets = INCOME_LABELS
    elif section == "bs":
        label_sets = BALANCE_LABELS
    else:
        return candidates

    # Detect current-year column from header
    header = [str(cell or "").strip() for cell in table[0]]
    year_col_idx = None
    best_year = 0
    for idx, h in enumerate(header):
        m = re.search(r"20(\d{2})", h)
        if m:
            yr = int("20" + m.group(1))
            if yr > best_year:
                best_year = yr
                year_col_idx = idx

    for row in table[1:]:
        if not row:
            continue
        label_cell = ""
        for cell in row:
            if cell and str(cell).strip():
                label_cell = str(cell).strip()
                break
        if not label_cell:
            continue

        for metric, keywords in label_sets.items():
            if _label_matches(label_cell, keywords) is None:
                continue

            value = None
            if year_col_idx is not None and year_col_idx < len(row):
                value = parse_number(row[year_col_idx])

            if value is None:
                for idx, cell in enumerate(row[1:], start=1):
                    v = parse_number(cell)
                    if v is not None and abs(v) >= 100:
                        value = v
                        break

            if value is None:
                continue

            snippet = " | ".join(str(c or "").strip() for c in row if c)
            score = 2  # table gets base 2
            if metric in INCOME_LABELS and section == "pl":
                score += 2
            elif metric in BALANCE_LABELS and section == "bs":
                score += 2

            candidates.append(Candidate(
                metric=metric,
                value=value,
                page=page_number,
                snippet=snippet[:200],
                method="table",
                score=score,
            ))

    return candidates


# ───────────────────────────────────────────────────────────
# 6) NOTE-BLOCK EXTRACTION (Note 20 & Note 8)
# ───────────────────────────────────────────────────────────

def _find_note_block(
    full_text: str, note_pattern: str, end_pattern: str
) -> Optional[str]:
    """Isolate a note section from full document text."""
    match = re.search(note_pattern, full_text, re.IGNORECASE)
    if not match:
        return None
    start = match.start()
    end_match = re.search(end_pattern, full_text[match.end():], re.IGNORECASE)
    end = match.end() + end_match.start() if end_match else min(start + 3000, len(full_text))
    return full_text[start:end]


def _extract_note20_breakdown(full_text: str) -> Dict[str, Optional[float]]:
    """Extract the investment income breakdown from the Investment income note.

    Handles wrapped lines like:
      "Investment income from other financial assets measured at"
      "FVTOCI 14,133 11,644"
    by joining non-numeric lines with the next line.
    """
    result: Dict[str, Optional[float]] = {
        "investment_income_deposits": None,
        "investment_income_amortised_cost": None,
        "investment_income_fvtoci": None,
        "investment_income_total": None,
    }

    block = _find_note_block(
        full_text,
        r"\b\d+\.\s*Investment income\b",
        r"\b\d+\.\s*(?:Dividend income|General and administrative|Other income)\b",
    )
    if not block:
        return result

    # Merge wrapped lines: if a line has no numbers, append next line to it
    raw_lines = block.split("\n")
    merged: List[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            continue
        # If previous line has no numbers and is not a note heading, merge
        if (
            merged
            and not _NUM_RE.search(merged[-1])
            and not re.match(r"^\d+\.\s", merged[-1].strip())
            and not re.match(r"^AED", merged[-1].strip(), re.IGNORECASE)
        ):
            merged[-1] = merged[-1].rstrip() + " " + stripped
        else:
            merged.append(stripped)

    for line in merged:
        lowered = line.lower()
        nums = [parse_number(m) for m in _NUM_RE.findall(line)]
        nums = [n for n in nums if n is not None and abs(n) >= 100]

        # Filter out year values (2000-2099)
        nums = [n for n in nums if not (2000 <= n <= 2099)]
        if not nums:
            continue

        val = nums[0]  # first number = current year

        # Only set if not already set (first match wins)
        if ("from investment deposits" in lowered or "from deposits" in lowered) and result["investment_income_deposits"] is None:
            result["investment_income_deposits"] = val
        elif "amortised cost" in lowered and result["investment_income_amortised_cost"] is None:
            result["investment_income_amortised_cost"] = val
        elif ("fvtoci" in lowered or "fvoci" in lowered or "fair value through other comprehensive" in lowered) and result["investment_income_fvtoci"] is None:
            result["investment_income_fvtoci"] = val

    # Note total: numbers-only line (skip year headers like "2025 2024")
    _YEAR_ONLY_RE = re.compile(r"^[\s]*20\d{2}\s+20\d{2}[\s]*$")
    for line in merged:
        stripped = line.strip()
        # Skip year headers
        if _YEAR_ONLY_RE.match(stripped):
            continue
        # Skip "AED'000" header lines
        if "aed" in stripped.lower():
            continue
        if re.match(r"^[\d,.\s()-]+$", stripped):
            nums = [parse_number(m) for m in _NUM_RE.findall(stripped)]
            nums = [n for n in nums if n is not None and abs(n) >= 100]
            if nums:
                result["investment_income_total"] = nums[0]
                break

    return result


def _extract_note8_fvtoci_split(full_text: str) -> Dict[str, Optional[float]]:
    """Extract FVTOCI sub-components from Note 8.

    Returns fvtoci_equity, fvtoci_funds, fvtoci_sukuk, fvtoci_total.
    """
    result: Dict[str, Optional[float]] = {
        "fvtoci_equity": None,
        "fvtoci_funds": None,
        "fvtoci_sukuk": None,
        "fvtoci_total": None,
    }

    block = _find_note_block(
        full_text,
        r"\b\d+\.\s*Financial assets measured at fair value through other comprehensive income",
        r"\b\d+\.\s*Investments at amortised cost\b",
    )
    if not block:
        return result

    lines = block.split("\n")
    for line in lines:
        lowered = line.lower()
        nums = [parse_number(m) for m in _NUM_RE.findall(line)]
        nums = [n for n in nums if n is not None and abs(n) >= 100]

        if not nums:
            continue

        # Skip years that sneak in as valid numbers
        nums = [n for n in nums if not (2000 <= n <= 2099)]
        if not nums:
            continue

        val = nums[0]  # current year

        # Only set if not already set (first match = table row, not narrative)
        if "equity securities" in lowered and result["fvtoci_equity"] is None:
            result["fvtoci_equity"] = val
        elif "managed fund" in lowered and result["fvtoci_funds"] is None:
            result["fvtoci_funds"] = val
        elif "investment in sukuk" in lowered and result["fvtoci_sukuk"] is None:
            result["fvtoci_sukuk"] = val

    # Total: numbers-only line with a value > 1M (AED'000)
    _YEAR_ONLY_RE = re.compile(r"^[\s]*20\d{2}\s+20\d{2}[\s]*$")
    for line in lines:
        stripped = line.strip()
        if _YEAR_ONLY_RE.match(stripped):
            continue
        if "aed" in stripped.lower():
            continue
        if re.match(r"^[\d,.\s()-]+$", stripped):
            nums = [parse_number(m) for m in _NUM_RE.findall(stripped)]
            nums = [n for n in nums if n is not None and abs(n) >= 1_000_000]
            if nums:
                result["fvtoci_total"] = nums[0]
                break

    return result


# ───────────────────────────────────────────────────────────
# 7) BEST CANDIDATE SELECTION
# ───────────────────────────────────────────────────────────

def _best_candidates(candidates: List[Candidate]) -> Dict[str, Candidate]:
    """Select best candidate per metric with tie-breaking:
      1. Higher score wins
      2. Table beats regex (at same score)
      3. For balance metrics, larger absolute value wins (at same score+method)
    """
    _METHOD_RANK = {"table": 2, "note_block": 1, "regex": 0}
    best: Dict[str, Candidate] = {}

    for c in candidates:
        existing = best.get(c.metric)
        if existing is None:
            best[c.metric] = c
            continue

        if c.score > existing.score:
            best[c.metric] = c
        elif c.score == existing.score:
            c_rank = _METHOD_RANK.get(c.method, 0)
            e_rank = _METHOD_RANK.get(existing.method, 0)
            if c_rank > e_rank:
                best[c.metric] = c
            elif c_rank == e_rank and c.metric in BALANCE_LABELS:
                if abs(c.value) > abs(existing.value):
                    best[c.metric] = c

    return best


# ───────────────────────────────────────────────────────────
# 8) MAIN PARSE FUNCTION
# ───────────────────────────────────────────────────────────

def parse_pdf_financials(file) -> Dict[str, object]:
    """Parse a DFM financial statement PDF.

    Returns:
      metrics   – extracted values (AED'000)
      audit     – extraction details for debugging
      items     – human-readable summary strings
      note20    – investment income breakdown
      note8     – FVTOCI sub-component split
      warnings  – validation warnings
    """
    metrics: Dict[str, float] = {}
    audit: List[Dict[str, object]] = []
    items: List[str] = []
    warnings: List[str] = []
    candidates: List[Candidate] = []

    page_texts: List[str] = []
    page_sections: List[Optional[str]] = []

    with pdfplumber.open(file) as pdf:
        # PASS 1: Read + classify all pages
        for page in pdf.pages:
            text = page.extract_text() or ""
            page_texts.append(text)
            page_sections.append(_classify_page(text))

        # PASS 2: Extract candidates from primary statements only
        for page_idx, page in enumerate(pdf.pages):
            text = page_texts[page_idx]
            section = page_sections[page_idx]
            page_number = page_idx + 1

            if section not in ("pl", "bs"):
                continue

            col_count = _detect_column_count(text)
            lines = text.split("\n")

            candidates.extend(
                _extract_regex_candidates(lines, page_number, section, col_count)
            )

            for table in page.extract_tables() or []:
                candidates.extend(
                    _extract_table_candidates(table, page_number, section)
                )

    # PASS 3: Best candidates
    best = _best_candidates(candidates)

    for metric, candidate in best.items():
        metrics[metric] = candidate.value
        audit.append({
            "metric_name": metric,
            "value": candidate.value,
            "method": candidate.method,
            "page": candidate.page,
            "snippet": candidate.snippet,
            "confidence": f"score={candidate.score}",
        })

    # PASS 4: Period detection
    full_text = "\n".join(page_texts)
    metrics["period_months"] = _detect_period_months(full_text)

    # PASS 5: Note-block extraction
    note20 = _extract_note20_breakdown(full_text)
    note8 = _extract_note8_fvtoci_split(full_text)

    # Merge note breakdown into metrics
    for key in [
        "investment_income_deposits",
        "investment_income_amortised_cost",
        "investment_income_fvtoci",
    ]:
        if note20.get(key) is not None:
            metrics[key] = note20[key]

    for key in ["fvtoci_equity", "fvtoci_funds", "fvtoci_sukuk"]:
        if note8.get(key) is not None:
            metrics[key] = note8[key]

    # FVTOCI fallback: if BS extraction missed it, use Note 8 total
    if "fvtoci" not in metrics or metrics.get("fvtoci", 0) < 1000:
        if note8.get("fvtoci_total") is not None:
            metrics["fvtoci"] = note8["fvtoci_total"]
            audit.append({
                "metric_name": "fvtoci",
                "value": note8["fvtoci_total"],
                "method": "note_block",
                "page": None,
                "snippet": "FVTOCI total from Note 8 block",
                "confidence": "fallback",
            })

    # PASS 6: Validation
    headline = metrics.get("investment_income")
    if headline:
        # Check note total vs headline
        note_total = note20.get("investment_income_total")
        if note_total:
            diff = abs(headline - note_total)
            tol = max(abs(headline) * 0.005, 2)
            if diff > tol:
                warnings.append(
                    f"Note total ({note_total:,.0f}) ≠ headline investment "
                    f"income ({headline:,.0f}); Δ = {diff:,.0f}."
                )

        # Check breakdown sum vs headline
        bkdn = sum(
            note20.get(k) or 0
            for k in [
                "investment_income_deposits",
                "investment_income_amortised_cost",
                "investment_income_fvtoci",
            ]
        )
        if bkdn > 0:
            diff = abs(headline - bkdn)
            tol = max(abs(headline) * 0.005, 2)
            if diff > tol:
                warnings.append(
                    f"Breakdown sum ({bkdn:,.0f}) ≠ headline ({headline:,.0f}); "
                    f"Δ = {diff:,.0f}."
                )

    # Build display items
    if "trading_commission" in metrics:
        items.append(f"Trading Comm: {metrics['trading_commission']:,.0f}")
    if "investment_income" in metrics:
        items.append(f"Inv Income: {metrics['investment_income']:,.0f}")
    if "dividend_income" in metrics:
        items.append(f"Dividend Income: {metrics['dividend_income']:,.0f}")
    if "investment_deposits" in metrics:
        items.append(
            f"Investment Deposits (cash at banks): "
            f"{metrics['investment_deposits']:,.0f}"
        )
    if "investments_amortised_cost" in metrics:
        items.append(
            f"Investments at Amortised Cost (sukuk & bonds): "
            f"{metrics['investments_amortised_cost']:,.0f}"
        )
    if "fvtoci" in metrics:
        items.append(f"FVTOCI Financial Assets: {metrics['fvtoci']:,.0f}")
    if "cash_and_equivalents" in metrics:
        items.append(f"Cash & Equivalents: {metrics['cash_and_equivalents']:,.0f}")

    return {
        "metrics": metrics,
        "audit": audit,
        "items": items,
        "note20": note20,
        "note8": note8,
        "warnings": warnings,
    }


# ───────────────────────────────────────────────────────────
# 9) PORTFOLIO HELPERS
# ───────────────────────────────────────────────────────────

def compute_portfolio_from_metrics(metrics: Dict[str, float]) -> Optional[float]:
    """Total investment portfolio = deposits + amortised cost + FVTOCI."""
    return compute_portfolio([
        metrics.get("investment_deposits"),
        metrics.get("investments_amortised_cost"),
        metrics.get("fvtoci"),
    ])


def compute_ear_portfolio(metrics: Dict[str, float]) -> Optional[float]:
    """Earnings-at-Risk portfolio: rate-sensitive / income-generating only.
    = deposits + amortised cost + FVTOCI debt (sukuk).
    Excludes FVTOCI equities.
    """
    fvtoci_debt = metrics.get("fvtoci_sukuk", 0) or 0
    return compute_portfolio([
        metrics.get("investment_deposits"),
        metrics.get("investments_amortised_cost"),
        fvtoci_debt if fvtoci_debt > 0 else None,
    ])
