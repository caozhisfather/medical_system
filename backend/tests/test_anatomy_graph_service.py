from backend.app.knowledge_graph_service import AnatomyKnowledgeGraphService


def test_anatomy_graph_uses_learning_hierarchy() -> None:
    service = AnatomyKnowledgeGraphService()
    groups = {node["group"] for node in service.nodes}

    assert groups == {"AnatomyRoot", "AnatomySystem", "AnatomyOrgan", "AnatomyStructure"}
    assert sum(node["group"] == "AnatomySystem" for node in service.nodes) == 9
    assert sum(node["group"] == "AnatomyOrgan" for node in service.nodes) == 48
    assert all(edge["relation_zh"] in {"包含系统", "包含器官", "包含结构"} for edge in service.edges)


def test_anatomy_graph_search_reaches_heart_structures() -> None:
    service = AnatomyKnowledgeGraphService()
    matches = service.search_nodes("心脏")
    heart = next(node for node in matches if node["id"] == "anatomy_organ_heart")
    neighborhood = service.get_neighbors(heart["id"], depth=1)

    assert heart["label"] == "心脏"
    assert any(node["group"] == "AnatomyStructure" for node in neighborhood["nodes"])
    assert any(edge["source"] == heart["id"] for edge in neighborhood["edges"])
