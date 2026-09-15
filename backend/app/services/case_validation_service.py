from __future__ import annotations

from typing import Any


class CaseValidationService:
    def validate(self, case: dict[str, Any]) -> dict[str, Any]:
        checks = {
            "has_final_diagnosis": bool(case.get("hidden_final_diagnosis")),
            "has_three_differentials": len(case.get("differential_diagnoses", [])) >= 3,
            "has_five_scoring_points": len(case.get("key_scoring_points", [])) >= 5,
            "has_high_risk_misses": bool(case.get("high_risk_misses")),
            "has_source": bool(case.get("source")),
            "is_synthetic_teaching_case": case.get("source", {}).get("type") == "synthetic",
            "contains_no_real_identity": not case.get("source", {}).get("contains_real_patient_data", True),
        }
        return {
            "case_id": case.get("case_id", "candidate"),
            "valid": all(checks.values()),
            "checks": checks,
            "errors": [name for name, passed in checks.items() if not passed],
        }

