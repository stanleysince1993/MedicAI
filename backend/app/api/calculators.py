from fastapi import APIRouter, HTTPException
from ..schemas.calculator import CalculatorResponse
import json

router = APIRouter()

def calc_bmi(inputs: dict):
    # weight kg, height cm
    w = float(inputs.get("weight_kg")); h_cm = float(inputs.get("height_cm"))
    h_m = h_cm/100.0
    bmi = w/(h_m*h_m)
    flags = []
    if bmi < 18.5: flags.append("low")
    if bmi >= 30: flags.append("high")
    return bmi, "kg/m2", flags

TOOLS = {"bmi": calc_bmi}

@router.get("")
def calculate(tool: str, inputs: str | None = None):
    if tool not in TOOLS:
        raise HTTPException(404, "Calculator not found")
    data = json.loads(inputs or "{}" )
    value, units, flags = TOOLS[tool](data)
    return CalculatorResponse(tool=tool, value=value, units=units, flags=flags)
