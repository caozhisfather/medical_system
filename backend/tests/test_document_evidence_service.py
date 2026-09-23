from backend.app.services.document_evidence_service import DocumentEvidenceService


def test_natural_language_query_extracts_medical_terms() -> None:
    terms = DocumentEvidenceService._terms("心脏有哪些功能")

    assert "心脏" in terms
    assert "功能" in terms
    assert "哪些" not in terms


def test_body_content_outranks_atlas_front_matter() -> None:
    service = DocumentEvidenceService()
    front_matter = (
        "前言\n"
        "Netter 医生是外科医生，Machado 医生是心脏病学专家。"
        "新版增加了心脏的多个新视点。"
    )
    body_content = "\n".join(
        [
            "心脏是循环系统的动力器官。",
            "心脏位于纵隔内，外形呈倒置圆锥形。",
            "心脏由左右心房和左右心室构成。",
            "心脏传导系统负责产生并传导冲动。",
            "心脏壁由心内膜、心肌膜和心外膜组成。",
            "心脏的临床检查包括心电图和超声心动图。",
        ]
    )

    front_score = service._lexical_score(
        "心脏",
        front_matter,
        "奈特人体解剖学彩色图谱 第8版中文版",
        "textbook",
        "解剖图谱",
    )
    body_score = service._lexical_score(
        "心脏",
        body_content,
        "组织学与胚胎学（第10版）",
        "textbook",
        "教材",
    )

    assert body_score > front_score


def test_textbook_body_outranks_clinical_guideline_title() -> None:
    service = DocumentEvidenceService()
    textbook_score = service._lexical_score(
        "心脏",
        "心脏位于纵隔内。心脏由左右心房和左右心室构成。心脏壁分为三层。",
        "组织学与胚胎学（第10版）",
        "textbook",
        "教材",
    )
    guideline_score = service._lexical_score(
        "心脏",
        "心脏病患者接受非心脏手术时应评估心血管风险。",
        "心脏病患者非心脏手术围麻醉期中国专家临床管理共识",
        "evidence",
        "临床指南",
    )

    assert textbook_score > guideline_score
