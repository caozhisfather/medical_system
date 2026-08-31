from __future__ import annotations

from typing import Any


UNKNOWN_ANSWER = "这个我不太清楚，医生您能再具体问一下吗？"


class PatientAgent:
    diagnosis_words = ("诊断", "什么病", "最终结果", "病名", "是不是得了")
    routes = (
        (("主诉", "哪里不舒服", "怎么了"), "chief_complaint"),
        (("现病史", "多久", "开始", "诱因", "经过", "加重", "缓解", "伴随", "性质", "部位", "放射", "频率", "尿色", "粪色", "规律", "持续", "突然"), "present_illness"),
        (("既往史", "以前得过", "基础病", "住院", "手术"), "past_history"),
        (("用药", "吃药", "药物", "停药"), "medication_history"),
        (("过敏", "药物过敏", "食物过敏"), "allergy_history"),
        (("个人史", "吸烟", "饮酒", "职业", "饮食", "运动"), "personal_history"),
        (("家族史", "遗传", "家里人"), "family_history"),
    )

    def answer(self, case: dict[str, Any], message: str) -> dict[str, Any]:
        question = message.strip()
        if any(word in question for word in self.diagnosis_words):
            return {
                "reply": "我不知道最终诊断，只能把我经历的症状和已知情况告诉您。",
                "matched_field": "diagnosis_guard",
                "revealed_diagnosis": False,
            }

        ordered = self._match_test(case, question)
        if ordered:
            return {
                "reply": f"已申请{ordered['test_name']}，结果：{ordered['result']}",
                "matched_field": "available_tests",
                "ordered_test": ordered["test_name"],
                "revealed_diagnosis": False,
            }

        for keywords, field in self.routes:
            if not any(keyword in question for keyword in keywords):
                continue
            if field == "chief_complaint":
                reply = f"我主要是{case['chief_complaint']}。"
            else:
                values = case["history"].get(field, [])
                reply = "；".join(values) if values else UNKNOWN_ANSWER
            return {
                "reply": self._apply_style(case, reply),
                "matched_field": f"history.{field}",
                "revealed_diagnosis": False,
            }

        if any(word in question for word in ("查体", "体格检查", "生命体征", "血压", "心率", "血氧")):
            return {
                "reply": "相应查体结果为：" + "；".join(case["physical_exam"]),
                "matched_field": "physical_exam",
                "revealed_diagnosis": False,
            }

        for fact in case["history"]["present_illness"]:
            tokens = [token for token in case["symptom_tags"] if token in question]
            if tokens or any(part in question for part in ("疼", "喘", "咳", "热", "吐", "晕", "肿", "尿", "便")):
                return {
                    "reply": self._apply_style(case, fact),
                    "matched_field": "history.present_illness",
                    "revealed_diagnosis": False,
                }

        return {
            "reply": case.get("patient_answer_rules", {}).get("unknown_answer", UNKNOWN_ANSWER),
            "matched_field": "unknown",
            "revealed_diagnosis": False,
        }

    def order_test(self, case: dict[str, Any], test_name: str) -> dict[str, Any]:
        matched = next(
            (
                test
                for test in case["available_tests"]
                if test["test_name"] == test_name or test_name in test["test_name"]
            ),
            None,
        )
        if not matched:
            return {
                "available": False,
                "test_name": test_name,
                "result": "当前病例脚本未配置该项检查结果。",
            }
        return {"available": True, **matched}

    @staticmethod
    def _match_test(case: dict[str, Any], question: str) -> dict[str, Any] | None:
        if not any(word in question for word in ("申请", "检查", "化验", "结果", "查一下", "做个")):
            return None
        return next(
            (
                test
                for test in case["available_tests"]
                if any(keyword in question for keyword in test["trigger_keywords"])
            ),
            None,
        )

    @staticmethod
    def _apply_style(case: dict[str, Any], reply: str) -> str:
        style = case["patient_profile"]["communication_style"]
        if "紧张" in style or "焦虑" in style:
            return f"我有点担心。{reply}"
        if "短" in style or "停顿" in style or "迟缓" in style:
            return reply.split("；", 1)[0] + "。"
        return reply



