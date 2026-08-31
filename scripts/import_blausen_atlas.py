from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image


SOURCE = Path(r"E:\18_本科计算机专业课程笔记\07_竞赛\全球人工智能算法精英赛\八大系统解剖素材包_Blausen_20260812\anatomy_assets_20260812_blausen")
PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "frontend" / "src" / "assets" / "medical" / "anatomy" / "blausen20260812"
MANIFEST = PROJECT / "frontend" / "src" / "data" / "blausenAtlasAssets.ts"
GRAPH_MANIFEST = PROJECT / "data" / "anatomy_asset_graph.json"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with (SOURCE / "解剖图登记表.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            filename = row.get("本地文件名", "").strip()
            if not filename:
                continue
            source = SOURCE / "images" / next(
                (folder for folder in (SOURCE / "images").iterdir() if (folder / filename).exists()), ""
            ) / filename
            if not source.exists():
                continue
            target = OUTPUT / f"{row['编号']}.webp"
            if not target.exists():
                with Image.open(source) as image:
                    image = image.convert("RGB")
                    image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
                    image.save(target, "WEBP", quality=84, method=6)
            rows.append({
                "id": row["编号"],
                "system": row["所属系统"],
                "topic": row["器官/结构"],
                "filename": filename,
                "asset": f"./assets/medical/anatomy/blausen20260812/{row['编号']}.webp",
                "source": row.get("原始文件页", ""),
                "license": row.get("授权协议", "待核对授权"),
                "status": row.get("审核状态", "已下载待审核"),
                "level": row.get("建议层级", "器官"),
            })
    lines = [
        "export interface BlausenAtlasAsset {",
        "  id: string; system: string; topic: string; filename: string; asset: string; source: string; license: string; status: string; level: string;",
        "}",
        "",
        "export const blausenAtlasAssets: BlausenAtlasAsset[] = " + repr(rows).replace("'", "\"") + ";",
        "",
    ]
    MANIFEST.write_text("\n".join(lines), encoding="utf-8")
    systems = sorted({item["system"] for item in rows})
    graph_nodes = [
        {"id": f"anatomy_system_{system}", "label_zh": system, "label_en": system, "type": "anatomy_system", "group": "解剖系统", "summary": f"{system}解剖素材与分层结构"}
        for system in systems
    ]
    graph_nodes.extend({"id": f"anatomy_asset_{item['id']}", "label_zh": item["topic"], "label_en": item["topic"], "type": "anatomy_asset", "group": "解剖素材", "summary": f"{item['topic']} · {item['level']}", "source_ids": [item["id"]], "asset_id": item["id"], "asset_url": item["source"], "license": item["license"]} for item in rows)
    graph_edges = [{"source": f"anatomy_system_{item['system']}", "target": f"anatomy_asset_{item['id']}", "relation_zh": "包含解剖素材", "relation_en": "contains anatomy asset", "evidence_source": item["id"]} for item in rows]
    GRAPH_MANIFEST.write_text(json.dumps({"nodes": graph_nodes, "edges": graph_edges}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Imported {len(rows)} assets into {OUTPUT}")


if __name__ == "__main__":
    main()
