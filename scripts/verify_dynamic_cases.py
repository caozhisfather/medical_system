from __future__ import annotations

import json
import sys
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"


def request(path: str, payload: dict[str, Any] | None = None) -> Any:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def run_case(case_id: str, question: str) -> dict[str, Any]:
    started = request(
        "/api/training/start",
        {"case_id": case_id, "variant_id": "B", "difficulty": "标准", "mode": "完整训练"},
    )
    session_id = started["session_id"]
    chatted = request(
        "/api/training/chat",
        {
            "case_id": case_id,
            "session_id": session_id,
            "variant_id": "B",
            "message": question,
            "history": [],
        },
    )
    test_name = started["case"]["available_tests"][0]["test_name"]
    ordered = request("/api/training/order-test", {"session_id": session_id, "test_name": test_name})
    scored = request(
        "/api/training/submit-diagnosis",
        {
            "session_id": session_id,
            "preliminary_diagnosis": started["case"]["hidden_final_diagnosis"],
            "differentials": started["case"]["differential_diagnoses"][:3],
            "treatment_principles": "先完成风险评估，再根据检查结果制定教学处置原则",
            "citations": started["case"]["recommended_guidelines"][:1],
        },
    )
    guarded = request(
        "/api/training/chat",
        {
            "case_id": case_id,
            "session_id": session_id,
            "variant_id": "B",
            "message": "你最终是什么病？",
            "history": [],
        },
    )
    unknown = request(
        "/api/training/chat",
        {
            "case_id": case_id,
            "session_id": session_id,
            "variant_id": "B",
            "message": "你小时候最喜欢什么颜色？",
            "history": [],
        },
    )
    assert chatted["case_id"] == case_id
    assert chatted["variant_id"] == "B"
    assert chatted["revealed_diagnosis"] is False
    assert ordered["available"] is True
    assert scored["case_id"] == case_id
    assert scored["diagnosis_match"] is True
    assert started["case"]["hidden_final_diagnosis"] not in guarded["patient_reply"]["content"]
    assert unknown["patient_reply"]["content"] == "这个我不太清楚，医生您能再具体问一下吗？"
    return {
        "case_id": case_id,
        "opening": started["opening_statement"],
        "reply": chatted["patient_reply"]["content"],
        "test": f"{ordered['test_name']}：{ordered['result']}",
        "score": scored["total_score"],
    }


def main() -> None:
    cases = request("/api/cases")
    assert len(cases) >= 40
    validation = request("/api/admin/cases/validate", {})
    assert validation["valid"] is True and validation["count"] == len(cases)
    jaundice = request(f"/api/cases/search?q={quote('黄疸')}")
    assert any(item["case_id"] == "jaundice_case" for item in jaundice["items"])
    variants = request("/api/cases/jaundice_case/variants")
    assert [item["variant_id"] for item in variants["variants"]] == ["A", "B", "C"]

    results = [
        run_case("emergency_chest_pain", "疼痛是什么性质，会放射到哪里？"),
        run_case("jaundice_case", "尿色和粪便颜色有什么变化？"),
        run_case("dyspnea", "平卧后呼吸困难会加重吗？"),
    ]
    assert len({item["opening"] for item in results}) == 3
    assert len({item["reply"] for item in results}) == 3
    assert len({item["test"] for item in results}) == 3

    open_jaundice = request(
        "/api/agent/chat",
        {"message": "打开黄疸病例", "role": "student", "active_module": "router"},
    )
    assert open_jaundice["target_case_id"] == "jaundice_case"
    random_respiratory = request(
        "/api/agent/chat",
        {"message": "随机给我一个呼吸困难病例", "role": "student", "active_module": "router"},
    )
    selected = next(item for item in cases if item["case_id"] == random_respiratory["target_case_id"])
    assert "呼吸困难" in selected["symptom_tags"]

    print(
        json.dumps(
            {
                "case_count": len(cases),
                "validation": validation["valid"],
                "cross_case_results": results,
                "agent_targets": {
                    "jaundice": open_jaundice["target_case_id"],
                    "random_respiratory": random_respiratory["target_case_id"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        raise

