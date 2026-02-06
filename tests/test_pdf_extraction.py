from pathlib import Path

import pytest

from parsers.pdf_financials import compute_portfolio_from_metrics, parse_pdf_financials

FIXTURES = sorted(str(path) for path in Path("tests/fixtures").glob("*.pdf"))


def _find_fixture(name_fragment: str) -> Path:
    return next(
        path
        for path in Path("tests/fixtures").glob("*.pdf")
        if name_fragment in path.name
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


def test_pdf_extraction_values_for_2025_fixture():
    path = _find_fixture("DFM FS 2025")
    result = parse_pdf_financials(path)
    metrics = result.get("metrics", {})

    assert metrics.get("trading_commission") == 402951
    assert metrics.get("investment_income") == 221239
    assert metrics.get("dividend_income") == 54619
    assert metrics.get("finance_income") == 10183
    assert metrics.get("investment_deposits") == 4111622
    assert metrics.get("investments_amortised_cost") == 470186
    assert metrics.get("fvtoci") == 1470289
