from pathlib import Path

import pytest

from parsers.pdf_financials import compute_portfolio_from_metrics, parse_pdf_financials

FIXTURES = sorted(
    str(path) for path in Path("tests/fixtures").glob("*.pdf")
)


@pytest.mark.parametrize("fixture_path", FIXTURES)
def test_pdf_extraction_has_core_metrics(fixture_path):
    path = Path(fixture_path)
    result = parse_pdf_financials(path)
    metrics = result.get("metrics", {})

    assert metrics.get("trading_commission")
    assert metrics.get("investment_income")

    portfolio = compute_portfolio_from_metrics(metrics)
    assert portfolio and portfolio > 0

    audit = result.get("audit", [])
    assert audit
