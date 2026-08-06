"""Price parsing helpers."""

from __future__ import annotations

import re


class PriceParser:
    """Normalizes currency strings into floats."""

    _PRICE_PATTERN = re.compile(r"[\d,]+\.?\d*")

    @classmethod
    def parse(cls, raw_price: str | None) -> float | None:
        # Extracts the first numeric value from a currency string (e.g. "$1,299.99" → 1299.99).
        if not raw_price:
            return None

        cleaned = raw_price.replace("\xa0", " ").strip()
        match = cls._PRICE_PATTERN.search(cleaned)
        if not match:
            return None

        numeric = match.group(0).replace(",", "")
        try:
            return float(numeric)
        except ValueError:
            return None

    @classmethod
    def is_within_budget(cls, raw_price: str | None, max_price: float) -> bool:
        # Returns True when the parsed price exists and is less than or equal to max_price.
        parsed = cls.parse(raw_price)
        return parsed is not None and parsed <= max_price
