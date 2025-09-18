import math

import pytest

from backend.services.calculators import calculators, CalculatorError


def test_bmi_normal_range():
    result = calculators.calculate("bmi", {"weight_kg": 70, "height_cm": 170})
    assert result["tool"] == "bmi"
    assert math.isclose(result["value"], 24.2, rel_tol=1e-3)
    assert result["flags"] == []


def test_bmi_flags_underweight():
    result = calculators.calculate("bmi", {"weight_kg": 50, "height_cm": 180})
    assert "low" in result["flags"]


def test_egfr_reference_case():
    result = calculators.calculate("egfr", {
        "creatinine_mg_dl": 1.0,
        "age": 45,
        "sex": "male",
    })
    assert result["tool"] == "egfr"
    assert math.isclose(result["value"], 94.4, rel_tol=0.05)
    assert "low" not in result["flags"]


def test_egfr_critical_flag():
    result = calculators.calculate("egfr", {
        "creatinine_mg_dl": 2.6,
        "age": 72,
        "sex": "female",
    })
    assert "critical" in result["flags"]


def test_cha2ds2_vasc_high_risk_female():
    result = calculators.calculate("cha2ds2-vasc", {
        "age": 78,
        "sex": "female",
        "congestive_heart_failure": True,
        "hypertension": True,
        "diabetes": True,
        "stroke_tia": False,
        "vascular_disease": True,
    })
    assert result["value"] >= 5
    assert "high" in result["flags"]


def test_cha2ds2_vasc_low_risk_male():
    result = calculators.calculate("cha2ds2-vasc", {
        "age": 45,
        "sex": "male",
        "congestive_heart_failure": False,
        "hypertension": False,
        "diabetes": False,
        "stroke_tia": False,
        "vascular_disease": False,
    })
    assert result["value"] == 0
    assert "low" in result["flags"]


def test_curb65_high_risk():
    result = calculators.calculate("curb-65", {
        "confusion": True,
        "urea_mmol_l": 10,
        "respiratory_rate": 32,
        "systolic_bp": 85,
        "diastolic_bp": 55,
        "age": 70,
    })
    assert result["value"] >= 4
    assert "critical" in result["flags"]


def test_curb65_low_risk():
    result = calculators.calculate("curb-65", {
        "confusion": False,
        "urea_mmol_l": 5,
        "respiratory_rate": 20,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "age": 40,
    })
    assert result["value"] == 0
    assert "low" in result["flags"]


def test_calculator_unknown_tool():
    with pytest.raises(CalculatorError):
        calculators.calculate("unknown", {})


def test_calculator_invalid_json_inputs():
    with pytest.raises(CalculatorError):
        calculators.calculate("bmi", {"weight_kg": -10, "height_cm": 170})
