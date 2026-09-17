from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def _load(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class KnowledgeGraphService:
    def __init__(self) -> None:
        bilingual = DATA_DIR / "medical_kg_bilingual.json"
        self.graph = _load("medical_kg_bilingual.json") if bilingual.exists() else _load("medical_kg.json")
        self.nodes = self.graph["nodes"]
        self.edges = self.graph["edges"]

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        return next((node for node in self.nodes if node["id"] == node_id), None)

    def _node_text(self, node: dict[str, Any]) -> str:
        return " ".join([
            node.get("id", ""),
            node.get("label", ""),
            node.get("label_zh", ""),
            node.get("label_en", ""),
            node.get("summary", ""),
            node.get("description_zh", ""),
            node.get("description_en", ""),
            node.get("embedding_text", ""),
            node.get("embedding_text_zh", ""),
            node.get("embedding_text_en", ""),
            " ".join(node.get("aliases_zh", [])),
            " ".join(node.get("aliases_en", [])),
            " ".join(node.get("source_ids", [])),
            " ".join(node.get("related_case_ids", [])),
            " ".join(node.get("related_knowledge_ids", [])),
        ]).lower()

    @staticmethod
    def label(node: dict[str, Any], lang: str = "zh") -> str:
        if lang == "en":
            return node.get("label_en") or node.get("label") or node.get("id", "")
        return node.get("label_zh") or node.get("label") or node.get("id", "")

    def search_nodes(self, query: str = "", node_type: str = "", lang: str = "zh") -> list[dict[str, Any]]:
        q = query.lower().strip()
        result = []
        for node in self.nodes:
            node_group = node.get("group") or node.get("type")
            type_ok = not node_type or node_type == "全部" or node_group == node_type or node.get("type") == node_type
            query_ok = not q or q in self._node_text(node) or any(token and token.lower() in self._node_text(node) for token in query.split())
            if type_ok and query_ok:
                result.append({**node, "label": self.label(node, lang), "group": node_group})
        return result[:30]

    def get_neighbors(self, node_id: str, depth: int = 1, lang: str = "zh") -> dict[str, Any]:
        frontier = {node_id}
        seen = {node_id}
        selected_edges = []
        for _ in range(max(depth, 1)):
            next_frontier = set()
            for edge in self.edges:
                if edge["source"] in frontier or edge["target"] in frontier:
                    selected_edges.append({
                        **edge,
                        "relation": edge.get("relation_en") if lang == "en" else edge.get("relation_zh", edge.get("relation", "关联")),
                    })
                    next_frontier.add(edge["source"])
                    next_frontier.add(edge["target"])
            frontier = next_frontier - seen
            seen |= next_frontier
        nodes = []
        for node in self.nodes:
            if node["id"] in seen:
                node_group = node.get("group") or node.get("type")
                nodes.append({**node, "label": self.label(node, lang), "group": node_group})
        return {"nodes": nodes, "edges": selected_edges}

    def build_learning_path(self, query: str, lang: str = "zh") -> list[str]:
        nodes = self.search_nodes(query, lang=lang)[:8]
        if not nodes:
            nodes = [
                {**node, "label": self.label(node, lang), "group": node.get("group") or node.get("type")}
                for node in self.nodes[:8]
            ]
        return [node["label"] for node in nodes[:8]]


class AnatomyKnowledgeGraphService(KnowledgeGraphService):
    SYSTEMS = {
        "locomotor": ("运动系统", "Locomotor system", "骨、关节与相关支架结构"),
        "circulatory": ("循环系统", "Circulatory system", "心脏、动脉与静脉构成的运输网络"),
        "respiratory": ("呼吸系统", "Respiratory system", "气道、肺与气体交换相关结构"),
        "digestive": ("消化系统", "Digestive system", "消化管及其附属器官"),
        "urinary": ("泌尿系统", "Urinary system", "肾、输尿管、膀胱与尿道"),
        "reproductive": ("生殖系统", "Reproductive system", "生殖腺、输送管道与附属器官"),
        "nervous": ("神经系统", "Nervous system", "中枢神经结构及其组成"),
        "endocrine": ("内分泌系统", "Endocrine system", "产生并释放激素的器官"),
        "lymphatic": ("淋巴系统", "Lymphatic system", "淋巴回流与免疫相关器官"),
    }

    def __init__(self) -> None:
        anatomy_dir = ROOT_DIR / "frontend" / "public" / "anatomy"
        organs = json.loads((anatomy_dir / "organs.json").read_text(encoding="utf-8"))
        atlas = json.loads((anatomy_dir / "atlas.json").read_text(encoding="utf-8"))
        glossary_path = DATA_DIR / "anatomy_term_glossary.json"
        glossary_payload = json.loads(glossary_path.read_text(encoding="utf-8")) if glossary_path.exists() else {}
        glossary = glossary_payload.get("terms", glossary_payload)
        parts = {part["id"]: part for part in atlas.get("parts", [])}

        self.nodes = [{
            "id": "anatomy_root", "type": "AnatomyRoot", "group": "AnatomyRoot",
            "label": "人体解剖", "label_zh": "人体解剖", "label_en": "Human anatomy",
            "description_zh": "按人体系统、器官和精细结构组织的解剖学习图谱。",
        }]
        self.edges = []
        added_parts: set[str] = set()

        for group in organs.get("systems", []):
            system_id = group["system"]
            name_zh, name_en, summary = self.SYSTEMS.get(system_id, (system_id, system_id, "人体解剖系统"))
            system_node_id = f"anatomy_system_{system_id}"
            self.nodes.append({
                "id": system_node_id, "type": "AnatomySystem", "group": "AnatomySystem",
                "label": name_zh, "label_zh": name_zh, "label_en": name_en,
                "summary": summary, "description_zh": summary,
            })
            self.edges.append(self._edge("anatomy_root", system_node_id, "包含系统", "contains system", 1.0))

            for organ in group.get("organs", []):
                organ_node_id = f"anatomy_organ_{organ['id']}"
                self.nodes.append({
                    "id": organ_node_id, "type": "AnatomyOrgan", "group": "AnatomyOrgan",
                    "label": organ["name"], "label_zh": organ["name"],
                    "label_en": organ.get("nameEn", organ["name"]),
                    "summary": f"{name_zh}中的{organ['name']}，包含 {len(organ.get('partIds', []))} 个可交互精细结构。",
                    "description_zh": f"{organ['name']}属于{name_zh}，可在三维人体解剖中单独观察。",
                    "anatomy_system": system_id, "part_count": len(organ.get("partIds", [])),
                })
                self.edges.append(self._edge(system_node_id, organ_node_id, "包含器官", "contains organ", 0.95))

                for part_id in organ.get("partIds", []):
                    part = parts.get(part_id)
                    if not part:
                        continue
                    structure_node_id = f"anatomy_structure_{part_id}"
                    english = part.get("name", part_id)
                    chinese = glossary.get(english, english)
                    if part_id not in added_parts:
                        self.nodes.append({
                            "id": structure_node_id, "type": "AnatomyStructure", "group": "AnatomyStructure",
                            "label": chinese, "label_zh": chinese, "label_en": english,
                            "aliases_en": [english], "summary": f"{organ['name']}的三维精细结构。",
                            "description_zh": f"{chinese}是三维解剖模型中的可交互结构，英文名为 {english}。",
                            "anatomy_part_id": part_id, "anatomy_system": system_id,
                        })
                        added_parts.add(part_id)
                    self.edges.append(self._edge(organ_node_id, structure_node_id, "包含结构", "contains structure", 0.9))

        self.graph = {"nodes": self.nodes, "edges": self.edges}

    @staticmethod
    def _edge(source: str, target: str, relation_zh: str, relation_en: str, weight: float) -> dict[str, Any]:
        return {
            "source": source, "target": target, "relation": relation_zh,
            "relation_zh": relation_zh, "relation_en": relation_en,
            "weight": weight, "evidence_source": "bodyparts3d",
        }
