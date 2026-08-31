from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


class ObsidianGraphExportService:
    def __init__(self) -> None:
        self.graph = json.loads((DATA_DIR / "medical_kg_bilingual.json").read_text(encoding="utf-8"))

    def export_preview(self, limit: int = 12) -> dict[str, Any]:
        nodes = self.graph["nodes"][:limit]
        edges = self.graph["edges"]
        notes = []
        for node in nodes:
            links = [
                edge["target"] if edge["source"] == node["id"] else edge["source"]
                for edge in edges
                if edge["source"] == node["id"] or edge["target"] == node["id"]
            ][:10]
            lines = [
                "---",
                f"id: {node['id']}",
                f"type: {node.get('type', node.get('group', 'Knowledge'))}",
                f"source_ids: {', '.join(node.get('source_ids', []))}",
                "---",
                "",
                f"# {node.get('label_zh', node.get('label', node['id']))}",
                "",
                f"English: {node.get('label_en', '')}",
                "",
                node.get("description_zh", node.get("summary", "医学教育知识节点。")),
                "",
                "## 推荐关联",
            ]
            lines.extend([f"- [[{item}]]" for item in links])
            notes.append({"filename": f"{node['id']}.md", "content": "\n".join(lines)})
        return {
            "status": "mock_ready",
            "note_count": len(notes),
            "vault_name": "临思智训医学教育图谱",
            "notes": notes,
            "message": "已生成 Obsidian Markdown 预览，真实导出时可写入本地 vault 或对象存储。",
        }
