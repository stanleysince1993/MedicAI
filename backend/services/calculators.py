from typing import Any, Dict, List


class CalculatorError(ValueError):
    """Raised when calculator inputs are invalid."""


class CalculatorsService:
    SUPPORTED_TOOLS = {"bmi", "egfr", "cha2ds2-vasc", "curb-65"}

    def calculate(self, tool: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        tool_key = tool.lower()
        if tool_key not in self.SUPPORTED_TOOLS:
            raise CalculatorError(f"Unsupported calculator: {tool}")

        if tool_key == "bmi":
            return self._calculate_bmi(inputs)
        if tool_key == "egfr":
            return self._calculate_egfr(inputs)
        if tool_key == "cha2ds2-vasc":
            return self._calculate_cha2ds2_vasc(inputs)
        if tool_key == "curb-65":
            return self._calculate_curb65(inputs)
        raise CalculatorError(f"Unsupported calculator: {tool}")

    def _calculate_bmi(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            weight = float(inputs["weight_kg"])
            height_cm = float(inputs["height_cm"])
        except KeyError as exc:
            raise CalculatorError(f"Missing input: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise CalculatorError("Invalid numeric input for BMI") from exc

        if weight <= 0 or height_cm <= 0:
            raise CalculatorError("Weight and height must be positive values")

        height_m = height_cm / 100
        bmi = weight / (height_m ** 2)
        flags = self._flag_values(bmi, low=18.5, high=25.0, critical=35.0)

        return {
            "tool": "bmi",
            "value": round(bmi, 1),
            "units": "kg/m2",
            "flags": flags,
        }

    def _calculate_egfr(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        required = ["creatinine_mg_dl", "age", "sex"]
        for key in required:
            if key not in inputs:
                raise CalculatorError(f"Missing input: {key}")

        try:
            creatinine = float(inputs["creatinine_mg_dl"])
            age = float(inputs["age"])
        except (TypeError, ValueError) as exc:
            raise CalculatorError("Invalid numeric input for eGFR") from exc

        sex = str(inputs["sex"]).lower()
        race = str(inputs.get("race", "")).lower()

        if creatinine <= 0 or age <= 0:
            raise CalculatorError("Creatinine and age must be positive values")
        if sex not in {"male", "female"}:
            raise CalculatorError("Sex must be 'male' or 'female'")

        kappa = 0.7 if sex == "female" else 0.9
        alpha = -0.329 if sex == "female" else -0.411
        ratio = creatinine / kappa
        min_ratio = min(ratio, 1.0)
        max_ratio = max(ratio, 1.0)

        egfr = 141 * (min_ratio ** alpha) * (max_ratio ** -1.209) * (0.993 ** age)
        if sex == "female":
            egfr *= 1.018
        if race in {"black", "african_american"}:
            egfr *= 1.159

        egfr_value = round(egfr, 1)
        flags = self._flag_values(egfr_value, low=60, critical=30, high=120, invert=True)

        return {
            "tool": "egfr",
            "value": egfr_value,
            "units": "mL/min/1.73m2",
            "flags": flags,
        }

    def _calculate_cha2ds2_vasc(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        required_booleans = [
            "congestive_heart_failure",
            "hypertension",
            "diabetes",
            "stroke_tia",
            "vascular_disease",
        ]
        for key in required_booleans:
            if key not in inputs:
                raise CalculatorError(f"Missing input: {key}")

        try:
            age = int(inputs.get("age", 0))
        except (TypeError, ValueError) as exc:
            raise CalculatorError("Invalid age for CHA2DS2-VASc") from exc

        sex = str(inputs.get("sex", "")).lower()
        if sex not in {"male", "female"}:
            raise CalculatorError("Sex must be 'male' or 'female'")

        score = 0
        score += 2 if age >= 75 else 1 if 65 <= age <= 74 else 0
        score += 1 if inputs["congestive_heart_failure"] else 0
        score += 1 if inputs["hypertension"] else 0
        score += 1 if inputs["diabetes"] else 0
        score += 2 if inputs["stroke_tia"] else 0
        score += 1 if inputs["vascular_disease"] else 0
        score += 1 if sex == "female" else 0

        flags: List[str] = []
        if (sex == "male" and score >= 2) or (sex == "female" and score >= 3):
            flags.append("high")
        elif score == 1:
            flags.append("warning")
        else:
            flags.append("low")

        return {
            "tool": "cha2ds2-vasc",
            "value": score,
            "units": "points",
            "flags": flags,
        }

    def _calculate_curb65(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        required = [
            "confusion",
            "urea_mmol_l",
            "respiratory_rate",
            "systolic_bp",
            "diastolic_bp",
            "age",
        ]
        for key in required:
            if key not in inputs:
                raise CalculatorError(f"Missing input: {key}")

        try:
            urea = float(inputs["urea_mmol_l"])
            resp_rate = float(inputs["respiratory_rate"])
            sbp = float(inputs["systolic_bp"])
            dbp = float(inputs["diastolic_bp"])
            age = int(inputs["age"])
        except (TypeError, ValueError) as exc:
            raise CalculatorError("Invalid numeric input for CURB-65") from exc

        confusion = bool(inputs["confusion"])

        score = 0
        score += 1 if confusion else 0
        score += 1 if urea > 7.0 else 0
        score += 1 if resp_rate >= 30 else 0
        score += 1 if sbp < 90 or dbp <= 60 else 0
        score += 1 if age >= 65 else 0

        flags: List[str] = []
        if score >= 3:
            flags.append("critical")
        elif score == 2:
            flags.append("high")
        else:
            flags.append("low")

        return {
            "tool": "curb-65",
            "value": score,
            "units": "points",
            "flags": flags,
        }

    def _flag_values(
        self,
        value: float,
        *,
        low: float,
        high: float,
        critical: float,
        invert: bool = False,
    ) -> List[str]:
        flags: List[str] = []
        if invert:
            if value < critical:
                flags.append("critical")
            elif value < low:
                flags.append("low")
            elif value > high:
                flags.append("high")
        else:
            if value >= critical:
                flags.append("critical")
            elif value >= high:
                flags.append("high")
            elif value < low:
                flags.append("low")
        return flags


calculators = CalculatorsService()
