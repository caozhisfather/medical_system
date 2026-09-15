from __future__ import annotations

from typing import Any


class CaseSourceAdapter:
    """Maps reviewed public-source summaries into candidate teaching fields."""

    SOURCE_PLAN = [
        {
            "id": "modelscope_medical",
            "name": "ModelScope 医学数据集目录",
            "purpose": "医学问答、考试题和字段结构调研",
            "mode": "仅记录候选数据集元数据，不自动下载",
            "license_check_required": True,
        },
        {
            "id": "pmc_case_reports",
            "name": "PubMed Central 开放病例报告",
            "purpose": "病例叙事结构、检查和病程字段参考",
            "mode": "仅处理开放摘要并重新编写为合成病例",
            "license_check_required": True,
        },
        {
            "id": "medmcqa",
            "name": "MedMCQA",
            "purpose": "鉴别诊断问题和评分点结构参考",
            "mode": "不复制题干，先审查许可和用途",
            "license_check_required": True,
        },
        {
            "id": "pubmedqa",
            "name": "PubMedQA",
            "purpose": "循证问答和 citation 字段结构参考",
            "mode": "仅保留文献标识与自行摘要",
            "license_check_required": True,
        },
        {
            "id": "synthetic_medical",
            "name": "合成医学数据集合",
            "purpose": "虚拟患者沟通风格和对话轮次参考",
            "mode": "只接收明确标注为 synthetic 的候选内容",
            "license_check_required": True,
        },
    ]

    def plan(self) -> list[dict[str, Any]]:
        return self.SOURCE_PLAN

    def adapt(self, source: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": source.get("title", "待审核候选病例"),
            "summary": source.get("summary", ""),
            "source_id": source.get("source_id", "manual-mock"),
            "source_type": source.get("source_type", "synthetic"),
            "requires_human_review": True,
            "contains_identity_fields": False,
        }

