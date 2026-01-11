from __future__ import annotations

def parse_unit(value: str | float | int) -> float:
    """Parse monetary input allowing decimal comma (e.g. '37,05'). Returns float.

    Interprets the value as the main currency unit (e.g. NOK/kWh) and accepts
    a decimal comma. This name replaces the older `parse_ore` identifier.
    """
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if not s:
        raise ValueError("Empty value")

    # Allow thousands separators loosely (spaces) and decimal comma
    s = s.replace(" ", "").replace(",", ".")
    return float(s)

# Backwards-compatible alias for code that still calls the old name.
parse_ore = parse_unit
