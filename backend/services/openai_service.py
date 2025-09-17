import json
import os
from typing import Any, Dict, List

from pydantic import BaseModel

try:
    from openai import OpenAI  # type: ignore
except Exception:  # noqa: BLE001
    OpenAI = None  # type: ignore


SYSTEM_PROMPT = (
    "You are a clinical decision support assistant. Given a free-text clinical case, "
    "you will produce a concise differential diagnosis list and suggested diagnostic tests. "
    "Respond ONLY in valid JSON with keys: differentials (list of {condition, rationale, probability}), "
    "tests (list of {name, rationale}), and notes (string). Keep items succinct and high-signal."
)


class OpenAIAnalyzer:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if OpenAI is None:
            raise RuntimeError("openai package not available. Install 'openai'.")
        os.environ.setdefault("OPENAI_API_KEY", api_key)
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def analyze(self, case_text: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Clinical case:"\
                    f"\n{case_text}\n\n"
                    "Return compact JSON. Limit differentials to 3-5 with brief rationales."
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to coerce with a simple guard
            content = content.strip().strip("` ")
            data = json.loads(content)

        # Minimal normalization
        data.setdefault("differentials", [])
        data.setdefault("tests", [])
        data.setdefault("notes", "")
        return data


class FallbackAnalyzer:
    async def analyze(self, case_text: str) -> Dict[str, Any]:
        text_lower = case_text.lower()
        differentials: List[Dict[str, str]] = []
        tests: List[Dict[str, str]] = []

        # Very naive keyword heuristics for demo-only fallback
        if any(k in text_lower for k in ["dolor retroocular", "dengue", "plaquetas", "zika"]):
            differentials.append({
                "condition": "Dengue (probable)",
                "probability": "high",
                "rationale": "Fever with retro-orbital pain and endemic region",
            })
            tests.extend([
                {"name": "Serology Dengue IgM/IgG", "rationale": "Confirm acute infection"},
                {"name": "CBC with platelets", "rationale": "Assess thrombocytopenia"},
            ])

        if "fiebre" in text_lower and "persistente" in text_lower:
            differentials.append({
                "condition": "Typhoid fever",
                "probability": "medium",
                "rationale": "Persistent fever and systemic symptoms",
            })
            tests.append({"name": "Blood cultures", "rationale": "Detect Salmonella typhi"})

        if "linfadenopat" in text_lower or "adenopat" in text_lower:
            differentials.append({
                "condition": "Infectious mononucleosis",
                "probability": "low",
                "rationale": "Prolonged fever with lymphadenopathy",
            })
            tests.append({"name": "Monospot / EBV serology", "rationale": "Rule-in EBV"})

        if not differentials:
            differentials.append({
                "condition": "Undifferentiated febrile illness",
                "probability": "unknown",
                "rationale": "Insufficient specific features in the case description",
            })
            tests.append({
                "name": "Baseline labs (CBC, CMP)",
                "rationale": "Initial workup for fever of unknown origin",
            })

        return {
            "differentials": differentials[:5],
            "tests": tests[:5],
            "notes": "Fallback heuristic output. Provide more details for better results.",
        }



