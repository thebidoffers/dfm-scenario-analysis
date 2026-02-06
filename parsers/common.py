import re
from typing import Iterable, Optional

EMPTY_TOKENS = {"", "-", "–", "—", "na", "n/a"}


def parse_number(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    lower = text.lower().strip()
    if lower in EMPTY_TOKENS:
        return None
    text = text.replace(",", "").replace(" ", "")
    if re.fullmatch(r"[()\-–—\s]*", text):
        return None
    neg = False
    if text.startswith("(") and text.endswith(")"):
        neg = True
        text = text[1:-1]
    text = text.replace("–", "-").replace("—", "-")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    number = float(match.group(0))
    if neg:
        number = -abs(number)
    return number


def normalize_label(label: str) -> str:
    text = str(label or "").lower()
    text = re.sub(r"\bnote\s*\d+[a-z]*(?:\([a-z]\))?", "", text)
    text = re.sub(r"\b\d+\s*\([a-z]\)", "", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def label_matches(label: str, options: Iterable[str]) -> bool:
    normalized = normalize_label(label)
    for option in options:
        opt_norm = normalize_label(option)
        if opt_norm and opt_norm in normalized:
            return True
    return False


def compute_portfolio(components: Iterable[Optional[float]]) -> Optional[float]:
    values = [value for value in components if isinstance(value, (int, float))]
    if not values:
        return None
    return float(sum(values))
