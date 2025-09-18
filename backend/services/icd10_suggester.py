import re
from typing import Any, Dict, List, Optional


class ICD10Suggester:
    """Very lightweight keyword-based ICD-10 suggester for MVP purposes."""

    REVIEW_THRESHOLD = 0.6

    ICD10_CATALOG: List[Dict[str, Any]] = [
        {
            "code": "E11.9",
            "label": "Type 2 diabetes mellitus without complications",
            "keywords": ["diabetes", "hyperglycemia", "metformin"],
        },
        {
            "code": "I10",
            "label": "Essential (primary) hypertension",
            "keywords": ["hypertension", "high blood pressure", "htn"],
        },
        {
            "code": "J45.909",
            "label": "Unspecified asthma",
            "keywords": ["asthma", "wheezing", "bronchospasm"],
        },
        {
            "code": "J18.9",
            "label": "Pneumonia, unspecified organism",
            "keywords": ["pneumonia", "infiltrate", "consolidation"],
        },
        {
            "code": "I21.9",
            "label": "Acute myocardial infarction, unspecified",
            "keywords": ["stemi", "myocardial infarction", "troponin", "chest pain"],
        },
        {
            "code": "N18.3",
            "label": "Chronic kidney disease, stage 3",
            "keywords": ["ckd", "chronic kidney", "kidney disease"],
        },
        {
            "code": "E66.9",
            "label": "Obesity, unspecified",
            "keywords": ["obesity", "bmi", "weight gain"],
        },
        {
            "code": "F32.9",
            "label": "Major depressive disorder, single episode, unspecified",
            "keywords": ["depression", "anhedonia", "low mood"],
        },
        {
            "code": "A09",
            "label": "Infectious gastroenteritis and colitis, unspecified",
            "keywords": ["gastroenteritis", "diarrhea", "colitis"],
        },
        {
            "code": "R07.9",
            "label": "Chest pain, unspecified",
            "keywords": ["chest pain", "angina"],
        },
    ]

    def suggest(self, text: str, *, review_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        review_cutoff = review_threshold if review_threshold is not None else self.REVIEW_THRESHOLD
        normalized = text.lower()
        suggestions: List[Dict[str, Any]] = []

        for entry in self.ICD10_CATALOG:
            spans = self._find_spans(normalized, text, entry["keywords"])
            if not spans:
                continue

            confidence = self._score(entry["keywords"], spans)
            suggestions.append({
                "code": entry["code"],
                "label": entry["label"],
                "confidence": round(confidence, 2),
                "spans": spans,
                "needsReview": confidence < review_cutoff,
            })

        suggestions.sort(key=lambda item: item["confidence"], reverse=True)
        return suggestions

    def _find_spans(self, normalized: str, original: str, keywords: List[str]) -> List[Dict[str, Any]]:
        spans: List[Dict[str, Any]] = []
        for keyword in keywords:
            pattern = re.escape(keyword.lower())
            for match in re.finditer(pattern, normalized):
                start = match.start()
                end = match.end()
                spans.append({
                    "start": start,
                    "end": end,
                    "text": original[start:end],
                })
        return spans

    def _score(self, keywords: List[str], spans: List[Dict[str, Any]]) -> float:
        distinct_matches = len({span["text"].lower() for span in spans})
        base = distinct_matches / max(len(keywords), 1)
        return min(0.95, 0.4 + base * 0.5)


icd10_suggester = ICD10Suggester()
