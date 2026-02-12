"""
Tests for parsers.pdf_financials — Phase 1 overhaul.

Validates against three DFM PDF fixtures:
  1. DFM FS 2025 EN (annual, tests/fixtures)
  2. DFM FS 2025 EN (annual, uploaded copy)
  3. DFM Q3 2025 FS EN (interim, tests/fixtures)

Tests cover:
  - Correct year-column selection (annual 2-col, interim 4-col)
  - Section scoping (no OCI/cashflow false positives)
  - Note 20 investment income breakdown
  - Note 8 FVTOCI sub-component split
  - Reconciliation validation (Note 20 sum ≈ headline)
  - Portfolio computations (total and EaR)
"""

import os
import pytest

from parsers.pdf_financials import (
    parse_pdf_financials,
    compute_portfolio_from_metrics,
    compute_ear_portfolio,
)


# ───── Fixture paths ─────

ANNUAL_FS_FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "DFM FS 2025   EN.Pdf.pdf"
)
Q3_FS_FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "DFM Q3 2025 FS   EN..pdf"
)

# Also test the uploaded copy if present
ANNUAL_FS_UPLOADED = "/mnt/user-data/uploads/DFM_FS_2025___EN_Pdf.pdf"


def _has_fixture(path: str) -> bool:
    return os.path.isfile(path)


# ═══════════════════════════════════════════════════════════
# ANNUAL FS TESTS
# ═══════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def annual_result():
    """Parse the annual FS fixture once for all annual tests."""
    if not _has_fixture(ANNUAL_FS_FIXTURE):
        pytest.skip("Annual FS fixture not found")
    return parse_pdf_financials(ANNUAL_FS_FIXTURE)


class TestAnnualPrimaryStatements:
    """Test extraction from P&L and balance sheet (2-column annual layout)."""

    def test_trading_commission_is_2025_not_2024(self, annual_result):
        """Critical: must pick 402,951 (2025) not 232,140 (2024)."""
        assert annual_result["metrics"]["trading_commission"] == 402_951

    def test_investment_income_headline(self, annual_result):
        assert annual_result["metrics"]["investment_income"] == 221_239

    def test_dividend_income(self, annual_result):
        assert annual_result["metrics"]["dividend_income"] == 54_619

    def test_investment_deposits(self, annual_result):
        assert annual_result["metrics"]["investment_deposits"] == 4_111_622

    def test_investments_amortised_cost(self, annual_result):
        assert annual_result["metrics"]["investments_amortised_cost"] == 470_186

    def test_fvtoci_balance_not_oci_tax_line(self, annual_result):
        """Critical: must be 1,470,289 (BS balance), not -826 (OCI deferred tax)."""
        assert annual_result["metrics"]["fvtoci"] == 1_470_289

    def test_cash_and_equivalents(self, annual_result):
        assert annual_result["metrics"]["cash_and_equivalents"] == 183_315

    def test_finance_income(self, annual_result):
        assert annual_result["metrics"]["finance_income"] == 10_183

    def test_period_is_12_months(self, annual_result):
        assert annual_result["metrics"]["period_months"] == 12


class TestAnnualNote20Breakdown:
    """Test investment income breakdown from the Investment income note."""

    def test_income_from_deposits(self, annual_result):
        assert annual_result["metrics"]["investment_income_deposits"] == 192_248

    def test_income_from_amortised_cost(self, annual_result):
        assert annual_result["metrics"]["investment_income_amortised_cost"] == 14_858

    def test_income_from_fvtoci(self, annual_result):
        assert annual_result["metrics"]["investment_income_fvtoci"] == 14_133

    def test_note20_total_matches_headline(self, annual_result):
        """Note 20 total should equal headline investment income."""
        assert annual_result["note20"]["investment_income_total"] == 221_239

    def test_breakdown_sums_to_headline(self, annual_result):
        """Sum of breakdown components should equal headline."""
        breakdown_sum = (
            annual_result["note20"]["investment_income_deposits"]
            + annual_result["note20"]["investment_income_amortised_cost"]
            + annual_result["note20"]["investment_income_fvtoci"]
        )
        headline = annual_result["metrics"]["investment_income"]
        assert abs(breakdown_sum - headline) <= 2  # tolerance AED 2k

    def test_no_reconciliation_warnings(self, annual_result):
        """No warnings when everything reconciles."""
        assert len(annual_result["warnings"]) == 0


class TestAnnualNote8FVTOCISplit:
    """Test FVTOCI sub-component extraction from Note 8."""

    def test_fvtoci_equity(self, annual_result):
        assert annual_result["metrics"]["fvtoci_equity"] == 1_118_400

    def test_fvtoci_funds(self, annual_result):
        """Must be 25,127 (table row), not 2,024 (year in narrative)."""
        assert annual_result["metrics"]["fvtoci_funds"] == 25_127

    def test_fvtoci_sukuk(self, annual_result):
        assert annual_result["metrics"]["fvtoci_sukuk"] == 326_762

    def test_fvtoci_subcomponents_sum_to_total(self, annual_result):
        """Equity + funds + sukuk should equal FVTOCI total."""
        n8 = annual_result["note8"]
        sub_sum = n8["fvtoci_equity"] + n8["fvtoci_funds"] + n8["fvtoci_sukuk"]
        assert sub_sum == 1_470_289
        assert sub_sum == annual_result["metrics"]["fvtoci"]


class TestAnnualPortfolios:
    """Test portfolio computation helpers."""

    def test_total_portfolio(self, annual_result):
        """Deposits + AC + FVTOCI = 6,052,097."""
        total = compute_portfolio_from_metrics(annual_result["metrics"])
        assert total == 4_111_622 + 470_186 + 1_470_289

    def test_ear_portfolio(self, annual_result):
        """Deposits + AC + FVTOCI sukuk (debt only) = 4,908,570."""
        ear = compute_ear_portfolio(annual_result["metrics"])
        assert ear == 4_111_622 + 470_186 + 326_762

    def test_ear_excludes_fvtoci_equity(self, annual_result):
        """EaR should not include FVTOCI equity securities."""
        ear = compute_ear_portfolio(annual_result["metrics"])
        total = compute_portfolio_from_metrics(annual_result["metrics"])
        assert ear < total
        # Difference should be equity + funds
        diff = total - ear
        assert diff == 1_118_400 + 25_127


class TestAnnualAuditTrail:
    """Test that audit trail captures extraction method and page."""

    def test_audit_entries_exist(self, annual_result):
        assert len(annual_result["audit"]) > 0

    def test_each_audit_has_required_fields(self, annual_result):
        for entry in annual_result["audit"]:
            assert "metric_name" in entry
            assert "value" in entry
            assert "method" in entry
            assert "page" in entry
            assert "snippet" in entry

    def test_trading_commission_from_pl_page(self, annual_result):
        """Trading commission should be extracted from P&L page."""
        tc_audits = [
            a for a in annual_result["audit"]
            if a["metric_name"] == "trading_commission"
        ]
        assert len(tc_audits) == 1
        # P&L is page 8 in the 2025 annual
        assert tc_audits[0]["page"] == 8

    def test_fvtoci_from_bs_page(self, annual_result):
        """FVTOCI balance should be from BS (page 7), not OCI (page 9)."""
        fv_audits = [
            a for a in annual_result["audit"]
            if a["metric_name"] == "fvtoci"
        ]
        assert len(fv_audits) >= 1
        assert fv_audits[0]["page"] == 7


# ═══════════════════════════════════════════════════════════
# Q3 INTERIM FS TESTS
# ═══════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def q3_result():
    """Parse the Q3 interim FS fixture."""
    if not _has_fixture(Q3_FS_FIXTURE):
        pytest.skip("Q3 interim FS fixture not found")
    return parse_pdf_financials(Q3_FS_FIXTURE)


class TestQ3InterimPrimaryStatements:
    """Test 4-column interim layout picks YTD values correctly."""

    def test_trading_commission_is_9m_2025(self, q3_result):
        """Must pick 310,195 (9M-2025), not 113,272 (Q3) or 138,179 (9M-2024)."""
        assert q3_result["metrics"]["trading_commission"] == 310_195

    def test_investment_income_is_9m_2025(self, q3_result):
        """Must pick 165,348 (9M-2025), not 55,461 (Q3)."""
        assert q3_result["metrics"]["investment_income"] == 165_348

    def test_dividend_income_is_9m_2025(self, q3_result):
        assert q3_result["metrics"]["dividend_income"] == 51_521

    def test_investment_deposits(self, q3_result):
        """BS is 2-column even in interim."""
        assert q3_result["metrics"]["investment_deposits"] == 4_134_622

    def test_investments_amortised_cost(self, q3_result):
        assert q3_result["metrics"]["investments_amortised_cost"] == 367_717

    def test_fvtoci(self, q3_result):
        assert q3_result["metrics"]["fvtoci"] == 1_411_836

    def test_period_is_9_months(self, q3_result):
        assert q3_result["metrics"]["period_months"] == 9


class TestQ3InterimNote8:
    """Q3 interim should still extract Note 8 FVTOCI split."""

    def test_fvtoci_equity(self, q3_result):
        assert q3_result["metrics"]["fvtoci_equity"] == 1_111_095

    def test_fvtoci_sukuk(self, q3_result):
        assert q3_result["metrics"]["fvtoci_sukuk"] == 275_595

    def test_fvtoci_total_from_note8(self, q3_result):
        assert q3_result["note8"]["fvtoci_total"] == 1_411_836


class TestQ3InterimNote20:
    """Q3 interim doesn't have a Note 20 breakdown — should return None gracefully."""

    def test_note20_deposits_is_none(self, q3_result):
        assert q3_result["note20"]["investment_income_deposits"] is None

    def test_note20_amortised_cost_is_none(self, q3_result):
        assert q3_result["note20"]["investment_income_amortised_cost"] is None

    def test_note20_fvtoci_is_none(self, q3_result):
        assert q3_result["note20"]["investment_income_fvtoci"] is None

    def test_no_warnings_when_note20_missing(self, q3_result):
        """No false reconciliation warnings when Note 20 isn't present."""
        assert len(q3_result["warnings"]) == 0


# ═══════════════════════════════════════════════════════════
# UPLOADED COPY TEST (if available)
# ═══════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def uploaded_result():
    if not _has_fixture(ANNUAL_FS_UPLOADED):
        pytest.skip("Uploaded annual FS not available")
    return parse_pdf_financials(ANNUAL_FS_UPLOADED)


class TestUploadedAnnualFS:
    """Smoke test the uploaded copy matches the fixture copy."""

    def test_trading_commission_matches_fixture(self, uploaded_result):
        assert uploaded_result["metrics"]["trading_commission"] == 402_951

    def test_fvtoci_matches_fixture(self, uploaded_result):
        assert uploaded_result["metrics"]["fvtoci"] == 1_470_289

    def test_note20_breakdown_present(self, uploaded_result):
        assert uploaded_result["note20"]["investment_income_deposits"] == 192_248
