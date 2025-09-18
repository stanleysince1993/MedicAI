from __future__ import annotations

from typing import Any


class ObservationValidationError(ValueError):
    """Raised when an observation payload fails validation."""


ALLOWED_UNITS: dict[str, set[str]] = {
    "spo2": {"%"},
    "oxygen_saturation": {"%"},
    "heart_rate": {"bpm"},
    "hr": {"bpm"},
    "glucose": {"mg/dl", "mmol/l"},
    "weight": {"kg", "lb"},
    "temperature": {"c", "f"},
}

VALUE_LIMITS: dict[str, tuple[float | None, float | None]] = {
    "spo2": (0, 100),
    "oxygen_saturation": (0, 100),
    "heart_rate": (20, 260),
    "hr": (20, 260),
    "glucose": (20, 800),
    "temperature": (30, 45),
    "weight": (1, 500),
}


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def validate_observation(code: str, unit: str | None, value: Any) -> tuple[str, float | None]:
    """Validate observation code/unit/value and return normalized code and numeric value."""
    normalized_code = code.strip().lower()
    if not normalized_code:
        raise ObservationValidationError("Observation code is required")

    allowed_units = ALLOWED_UNITS.get(normalized_code)
    if allowed_units and unit:
        if unit.lower() not in {item.lower() for item in allowed_units}:
            allowed = ", ".join(sorted(allowed_units))
            raise ObservationValidationError(
                f"Unit '{unit}' is not allowed for {normalized_code}. Use one of: {allowed}."
            )

    numeric_value = _to_float(value)
    limits = VALUE_LIMITS.get(normalized_code)
    if limits:
        if numeric_value is None:
            raise ObservationValidationError(f"Value for {normalized_code} must be numeric.")
        lower, upper = limits
        if lower is not None and numeric_value < lower:
            raise ObservationValidationError(
                f"Value {numeric_value} is below the minimum {lower} accepted for {normalized_code}."
            )
        if upper is not None and numeric_value > upper:
            raise ObservationValidationError(
                f"Value {numeric_value} exceeds the maximum {upper} accepted for {normalized_code}."
            )

    return normalized_code, numeric_value


__all__ = ["ObservationValidationError", "validate_observation"]
