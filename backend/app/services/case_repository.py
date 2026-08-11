from __future__ import annotations

import copy
import json
import random
from pathlib import Path
from typing import Any

from ..config import ROOT_DIR


class CaseRepository:
    def __init__(self, data_file: Path | None = None) -> None:
        self.data_file = data_file or ROOT_DIR / "data" / "cases.json"

    def all(self) -> list[dict[str, Any]]:
        return json.loads(self.data_file.read_text(encoding="utf-8"))

    def get(self, case_id: str, variant_id: str | None = None) -> dict[str, Any]:
        case = next((item for item in self.all() if item["case_id"] == case_id), None)
        if case is None:
            raise KeyError(case_id)
        return self.apply_variant(case, variant_id)

    def search(
        self,
        query: str = "",
        department: str = "",
        symptom: str = "",
        difficulty: str = "",
        training_goal: str = "",
    ) -> list[dict[str, Any]]:
        query = query.strip().lower()
        result = []
        for case in self.all():
            haystack = " ".join(
                [
                    case["title_zh"],
                    case["title_en"],
                    case["chief_complaint"],
                    case["department"],
                    case["specialty"],
                    *case["symptom_tags"],
                    *case["training_goals"],
                    *case["differential_diagnoses"],
                ]
            ).lower()
            if query and query not in haystack:
                continue
            if department and department != case["department"]:
                continue
            if symptom and symptom not in case["symptom_tags"]:
                continue
            if difficulty and difficulty != case["difficulty"]:
                continue
            if training_goal and training_goal not in case["training_goals"]:
                continue
            result.append(case)
        return result

    def random(
        self,
        department: str = "",
        symptom: str = "",
        difficulty: str = "",
        training_goal: str = "",
    ) -> dict[str, Any]:
        candidates = self.search(
            department=department,
            symptom=symptom,
            difficulty=difficulty,
            training_goal=training_goal,
        )
        if not candidates:
            raise LookupError("没有符合筛选条件的病例")
        case = random.choice(candidates)
        variant_id = random.choice(["A", "B", "C"])
        return self.apply_variant(case, variant_id)

    @staticmethod
    def apply_variant(case: dict[str, Any], variant_id: str | None) -> dict[str, Any]:
        result = copy.deepcopy(case)
        selected = next(
            (item for item in result.get("case_variants", []) if item["variant_id"] == (variant_id or "A")),
            result.get("case_variants", [{}])[0],
        )
        if not selected:
            return result
        result["active_variant"] = selected["variant_id"]
        result["patient_profile"]["age"] = selected["age"]
        result["patient_profile"]["gender"] = selected["gender"]
        result["patient_profile"]["communication_style"] = selected["communication_style"]
        result["patient_profile_text"] = (
            f"{selected['age']}岁{selected['gender']}，"
            f"{result['patient_profile']['occupation']}，虚拟教学病例"
        )
        result["speaking_style"] = selected["communication_style"]
        result["opening_statement"] = selected["opening_statement"]
        result["opening"] = selected["opening_statement"]
        result["script"]["opening"] = selected["opening_statement"]
        present = result["history"]["present_illness"]
        if selected["variant_id"] == "B":
            result["history"]["present_illness"] = list(reversed(present))
        elif selected["variant_id"] == "C" and len(present) > 1:
            result["history"]["present_illness"] = [*present[1:], present[0]]
        result["present_illness"] = "；".join(result["history"]["present_illness"])
        if selected.get("distractor") and selected["variant_id"] != "A":
            result["history"]["personal_history"].append(selected["distractor"])
            result["personal_history"] = "；".join(result["history"]["personal_history"])
        return result



