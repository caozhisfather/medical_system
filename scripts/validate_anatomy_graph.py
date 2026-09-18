"""Validate the anatomy asset manifests before a competition demo."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    path = ROOT / relative
    with path.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"{relative} must contain a JSON object")
    return payload


def main() -> int:
    atlas = load("frontend/public/anatomy/atlas.json")
    organs = load("frontend/public/anatomy/organs.json")
    asset_graph = load("data/anatomy_asset_graph.json")
    glossary = load("data/anatomy_term_glossary.json")

    parts = atlas.get("parts") or []
    part_ids = [str(item.get("id") or "") for item in parts]
    if not parts or any(not part_id for part_id in part_ids):
        raise ValueError("atlas contains an empty part or part id")
    if len(part_ids) != len(set(part_ids)):
        raise ValueError("atlas part ids are not unique")

    systems = organs.get("systems") or []
    if len(systems) < 9:
        raise ValueError(f"expected at least 9 anatomy systems, got {len(systems)}")
    organ_ids: list[str] = []
    linked_parts: set[str] = set()
    for system in systems:
        for organ in system.get("organs") or []:
            organ_id = str(organ.get("id") or "")
            if not organ_id:
                raise ValueError("organ has no id")
            organ_ids.append(organ_id)
            for part_id in organ.get("partIds") or []:
                if part_id not in part_ids:
                    raise ValueError(f"organ {organ_id} references unknown part {part_id}")
                linked_parts.add(part_id)
    if len(organ_ids) != len(set(organ_ids)):
        raise ValueError("organ ids are not unique")
    # The teaching organ manifest intentionally groups the 48 headline organs;
    # it does not claim to classify every vessel, nerve and connective-tissue
    # part in the full atlas.
    if len(linked_parts) < len(part_ids) * 0.25:
        raise ValueError("organ manifest covers unexpectedly few atlas parts")

    graph_nodes = asset_graph.get("nodes") or []
    graph_ids = {str(node.get("id") or "") for node in graph_nodes}
    if not graph_nodes or "" in graph_ids:
        raise ValueError("asset graph contains an empty node id")
    for edge in asset_graph.get("edges") or []:
        if edge.get("source") not in graph_ids or edge.get("target") not in graph_ids:
            raise ValueError("asset graph contains an edge with an unknown endpoint")
        if not edge.get("relation_zh"):
            raise ValueError("asset graph edge has no Chinese relation label")

    terms = glossary.get("terms") or {}
    if len(terms) < 1000 or glossary.get("count") != len(terms):
        raise ValueError("anatomy glossary count is missing or unexpectedly small")

    print(
        json.dumps(
            {
                "result": "PASS",
                "atlas_parts": len(parts),
                "organ_systems": len(systems),
                "organs": len(organ_ids),
                "linked_parts": len(linked_parts),
                "asset_graph_nodes": len(graph_nodes),
                "asset_graph_edges": len(asset_graph.get("edges") or []),
                "glossary_terms": len(terms),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
