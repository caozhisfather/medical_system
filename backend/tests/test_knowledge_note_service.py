from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.app.services.knowledge_note_service import KnowledgeNoteService


def test_concurrent_note_updates_do_not_lose_entries(tmp_path: Path) -> None:
    path = tmp_path / "student_notes.json"
    service = KnowledgeNoteService(path)

    def write_note(index: int) -> None:
        service.upsert(
            "student01",
            {
                "document_id": f"document-{index}",
                "page": index + 1,
                "content": f"note-{index}",
                "annotations": [],
            },
            f"note-{index}",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(write_note, range(40)))

    notes = service.list("student01")

    assert len(notes) == 40
    assert {note["id"] for note in notes} == {f"note-{index}" for index in range(40)}
    assert not list(tmp_path.glob(".student_notes.json.*.tmp"))


def test_note_update_is_scoped_to_account(tmp_path: Path) -> None:
    service = KnowledgeNoteService(tmp_path / "student_notes.json")
    original = service.upsert(
        "student01",
        {"document_id": "doc-1", "page": 1, "content": "first", "annotations": []},
        "shared-id",
    )
    service.upsert(
        "student02",
        {"document_id": "doc-2", "page": 2, "content": "second", "annotations": []},
        "shared-id",
    )
    updated = service.upsert(
        "student01",
        {"document_id": "doc-1", "page": 1, "content": "updated", "annotations": []},
        original["id"],
    )

    assert updated["content"] == "updated"
    assert service.list("student01", document_id="doc-1", page=1)[0]["content"] == "updated"
    assert service.list("student02", document_id="doc-2", page=2)[0]["content"] == "second"
