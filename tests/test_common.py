from parsers.common import normalize_label, parse_number


def test_parse_number_variants():
    assert parse_number("1,234") == 1234
    assert parse_number("(1,234)") == -1234
    assert parse_number("1 234") == 1234
    assert parse_number("-") is None
    assert parse_number("–") is None
    assert parse_number("") is None


def test_normalize_label_strips_notes():
    assert normalize_label("Investment income 7(b)") == "investment income"
    assert normalize_label("Trading commission fees (note 7(b))") == "trading commission fees"
