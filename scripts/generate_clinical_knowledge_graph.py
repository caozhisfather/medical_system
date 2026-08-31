from __future__ import annotations

import hashlib
import json
import pprint
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT_DIR / "data" / "medical_kg_bilingual.json"
CASES_PATH = ROOT_DIR / "data" / "cases.json"
BACKEND_GRAPH_PATH = ROOT_DIR / "backend" / "app" / "data" / "graph.py"
FRONTEND_GRAPH_PATH = ROOT_DIR / "frontend" / "src" / "data" / "graph.ts"

GROUP_ALIASES = {
    "LabTest": "Exam",
    "Imaging": "Exam",
    "Drug": "Treatment",
}


def normalized_group(group: str) -> str:
    return GROUP_ALIASES.get(group, group)


def normalized_label(value: str) -> str:
    label = re.sub(r"\s+", "", str(value or "").strip())
    return re.sub(r"(?:待进一步评估|待评估|待排)$", "", label) or str(value or "").strip()


def stable_id(group: str, label: str) -> str:
    digest = hashlib.sha1(f"{group}:{label}".encode("utf-8")).hexdigest()[:12]
    return f"clinical_{group.lower()}_{digest}"


def enrich_graph(graph: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [dict(node) for node in graph.get("nodes", [])]
    edges = [dict(edge) for edge in graph.get("edges", [])]
    node_ids = {node["id"] for node in nodes}

    label_index: dict[tuple[str, str], str] = {}
    for node in nodes:
        group = normalized_group(str(node.get("group") or node.get("type") or "LearningObjective"))
        node["group"] = group
        label = str(node.get("label_zh") or node.get("label") or node["id"]).strip()
        label_index[(group, label.casefold())] = node["id"]

    edge_keys = {
        (edge.get("source"), edge.get("target"), edge.get("relation_zh") or edge.get("relation"))
        for edge in edges
    }

    def ensure_node(
        group: str,
        label: str,
        description: str,
        case_id: str,
        source_ids: list[str] | None = None,
    ) -> str:
        group = normalized_group(group)
        label = normalized_label(label)
        key = (group, label.casefold())
        node_id = label_index.get(key)
        if node_id:
            node = next(item for item in nodes if item["id"] == node_id)
            related = node.setdefault("related_case_ids", [])
            if case_id and case_id not in related:
                related.append(case_id)
            sources = node.setdefault("source_ids", [])
            for source_id in source_ids or []:
                if source_id not in sources:
                    sources.append(source_id)
            return node_id

        node_id = stable_id(group, label)
        suffix = 2
        while node_id in node_ids:
            node_id = f"{stable_id(group, label)}_{suffix}"
            suffix += 1
        node_ids.add(node_id)
        node = {
            "id": node_id,
            "type": group,
            "group": group,
            "label": label,
            "label_zh": label,
            "label_en": label,
            "aliases_zh": [label],
            "aliases_en": [label],
            "description_zh": description,
            "description_en": description,
            "embedding_text_zh": f"{label} {group} 医学教育 临床思维",
            "embedding_text_en": f"{label} {group} medical education clinical reasoning",
            "source_ids": list(source_ids or []),
            "related_case_ids": [case_id] if case_id else [],
            "related_knowledge_ids": [],
            "embedding_id": f"emb_{node_id}",
            "vector_status": "mock",
        }
        nodes.append(node)
        label_index[key] = node_id
        return node_id

    def relate(source: str, target: str, relation_zh: str, relation_en: str, case_id: str, weight: float) -> None:
        key = (source, target, relation_zh)
        if source == target or key in edge_keys:
            return
        edge_keys.add(key)
        edges.append(
            {
                "source": source,
                "target": target,
                "relation": relation_zh,
                "relation_zh": relation_zh,
                "relation_en": relation_en,
                "weight": weight,
                "evidence_source": case_id,
                "explanation_zh": f"该关系来自虚拟教学病例“{case_id}”的结构化病例脚本。",
                "explanation_en": f"This relation is derived from the structured synthetic teaching case {case_id}.",
            }
        )

    for case in cases:
        case_id = str(case["case_id"])
        title = str(case.get("title_zh") or case.get("title") or case_id)
        diagnosis_label = normalized_label(str(case.get("hidden_final_diagnosis") or f"{title}目标诊断"))
        department_label = str(case.get("department") or "临床医学")

        case_node = ensure_node("Case", title, str(case.get("scenario") or "虚拟医学教学病例。"), case_id)
        department_node = ensure_node(
            "Department",
            department_label,
            f"负责{title}相关教学训练的学科方向。",
            case_id,
        )
        diagnosis_node = ensure_node(
            "Disease",
            diagnosis_label,
            f"{title}虚拟教学病例的目标诊断，用于训练问题表征与鉴别诊断。",
            case_id,
        )
        treatment_node = ensure_node(
            "Treatment",
            f"{title}安全处置",
            "；".join(case.get("high_risk_misses") or ["评估病情稳定性并及时升级处置"]),
            case_id,
        )
        relate(case_node, department_node, "所属学科", "belongs to department", case_id, 0.7)
        relate(case_node, diagnosis_node, "目标诊断", "target diagnosis", case_id, 1.0)
        relate(diagnosis_node, treatment_node, "处理原则", "management principle", case_id, 0.9)

        symptom_nodes: list[str] = []
        for symptom in case.get("symptom_tags") or []:
            symptom_node = ensure_node(
                "Symptom",
                str(symptom),
                f"{symptom}可见于多个虚拟教学病例，需要结合病史、查体和检查进行鉴别。",
                case_id,
            )
            symptom_nodes.append(symptom_node)
            relate(case_node, symptom_node, "表现为", "presents with", case_id, 0.95)
            relate(symptom_node, diagnosis_node, "可能提示", "may indicate", case_id, 0.85)

        exam_nodes: list[str] = []
        for exam in case.get("available_tests") or []:
            exam_name = str(exam.get("test_name") or "").strip()
            if not exam_name:
                continue
            exam_node = ensure_node(
                "Exam",
                exam_name,
                f"用于{title}等虚拟病例的检查选择训练，结果必须结合临床情境解释。",
                case_id,
            )
            exam_nodes.append(exam_node)
            relate(diagnosis_node, exam_node, "需要检查", "requires examination", case_id, 0.95)
            relate(case_node, exam_node, "可申请检查", "available examination", case_id, 0.8)

        differential_nodes: list[str] = []
        for differential in case.get("differential_diagnoses") or []:
            differential_node = ensure_node(
                "Disease",
                str(differential),
                f"{title}训练中需要主动考虑的鉴别诊断。",
                case_id,
            )
            differential_nodes.append(differential_node)
            relate(diagnosis_node, differential_node, "需要鉴别", "must differentiate from", case_id, 0.9)
            for symptom_node in symptom_nodes[:1]:
                relate(symptom_node, differential_node, "需要鉴别", "requires differentiation", case_id, 0.72)

        guideline_nodes: list[str] = []
        for guideline in case.get("recommended_guidelines") or []:
            guideline_node = ensure_node(
                "Guideline",
                str(guideline),
                f"{title}教学反馈中的指南或教学路径依据，正式使用前需教师审核版本与适用范围。",
                case_id,
            )
            guideline_nodes.append(guideline_node)
            relate(diagnosis_node, guideline_node, "指南依据", "supported by guideline", case_id, 0.88)
            relate(treatment_node, guideline_node, "参考依据", "evidence reference", case_id, 0.82)

        for goal in (case.get("training_goals") or [])[:3]:
            goal_node = ensure_node(
                "LearningObjective",
                str(goal),
                f"通过{title}病例训练达成的临床思维学习目标。",
                case_id,
            )
            relate(case_node, goal_node, "训练目标", "learning objective", case_id, 0.75)
            for guideline_node in guideline_nodes[:1]:
                relate(goal_node, guideline_node, "证据支撑", "supported by evidence", case_id, 0.62)

        for exam_node in exam_nodes[:2]:
            for differential_node in differential_nodes[:2]:
                relate(differential_node, exam_node, "鉴别检查", "differential examination", case_id, 0.68)

    return {"nodes": nodes, "edges": edges}


def write_outputs(graph: dict[str, Any]) -> None:
    graph_json = json.dumps(graph, ensure_ascii=False, indent=2) + "\n"
    GRAPH_PATH.write_text(graph_json, encoding="utf-8")
    BACKEND_GRAPH_PATH.write_text(
        "MEDICAL_GRAPH = " + pprint.pformat(graph, width=120, sort_dicts=False) + "\n",
        encoding="utf-8",
    )
    FRONTEND_GRAPH_PATH.write_text(
        "export const mockGraph = " + graph_json.rstrip() + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    enriched = enrich_graph(graph, cases)
    write_outputs(enriched)
    counts: dict[str, int] = {}
    for node in enriched["nodes"]:
        group = str(node.get("group") or node.get("type") or "Unknown")
        counts[group] = counts.get(group, 0) + 1
    print(f"Generated {len(enriched['nodes'])} nodes and {len(enriched['edges'])} edges")
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
