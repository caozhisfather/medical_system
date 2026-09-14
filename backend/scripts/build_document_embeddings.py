"""Build a resumable Qwen embedding index for OCR'd medical documents."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.app.services.embedding_service import embedding_service  # noqa: E402

LIBRARY = ROOT / "data" / "document_library.json"
OCR_DIR = ROOT / "storage" / "document_ocr"
INDEX_META = ROOT / "data" / "document_embeddings.json"
INDEX_VECTORS = ROOT / "data" / "document_embeddings.npz"


def chunks(text: str, size: int = 1400, overlap: int = 180):
    text = text.strip()
    if not text:
        return
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        piece = text[start:end].strip()
        if piece:
            yield piece
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="仅处理前 N 个待生成文档")
    args = parser.parse_args()
    if not LIBRARY.exists():
        raise SystemExit("data/document_library.json 不存在，请先登记资料")
    library = json.loads(LIBRARY.read_text(encoding="utf-8"))
    documents = library.get("documents", [])
    old = json.loads(INDEX_META.read_text(encoding="utf-8")) if INDEX_META.exists() else {"items": [], "vectors_file": INDEX_VECTORS.name}
    old_items = {item["text_hash"]: item for item in old.get("items", []) if item.get("text_hash")}
    import numpy as np
    vectors_by_hash = {}
    if INDEX_VECTORS.exists() and old.get("items"):
        matrix = np.load(INDEX_VECTORS)["vectors"]
        for item, vector in zip(old["items"], matrix):
            if item.get("text_hash"):
                vectors_by_hash[item["text_hash"]] = vector

    pending = [doc for doc in documents if doc.get("ocr_status") == "completed" and doc.get("embedding_status") != "已生成"]
    if args.limit:
        pending = pending[: args.limit]
    processed = failed = 0
    for doc in pending:
        path = ROOT / doc["ocr_text_path"] if not Path(doc["ocr_text_path"]).is_absolute() else Path(doc["ocr_text_path"])
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            pending_texts = []
            records = []
            for page in payload.get("pages", []):
                for index, text in enumerate(chunks(page.get("text", ""))):
                    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    records.append({"document_id": doc["document_id"], "document_title": doc["title"], "page": page.get("page"), "chunk": index, "text": text, "text_hash": digest})
                    if digest not in vectors_by_hash:
                        pending_texts.append(text)
            if pending_texts:
                new_vectors = embedding_service.encode(pending_texts, batch_size=8)
                cursor = 0
                for record in records:
                    if record["text_hash"] not in vectors_by_hash:
                        vectors_by_hash[record["text_hash"]] = new_vectors[cursor]
                        cursor += 1
            doc["embedding_status"] = "已生成"
            doc["embedding_model"] = embedding_service.model
            doc["embedding_dimension"] = int(next(iter(vectors_by_hash.values())).shape[0]) if vectors_by_hash else 0
            doc["embedding_updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            old_items = {**old_items, **{record["text_hash"]: record for record in records}}
            processed += 1
            print(f"embedded {processed}: {doc['title']}", flush=True)
        except Exception as exc:
            doc["embedding_status"] = "生成失败"
            doc["embedding_error"] = str(exc)[:240]
            failed += 1
            print(f"failed {doc['title']}: {exc}", flush=True)

    items = list(old_items.values())
    matrix = np.asarray([vectors_by_hash[item["text_hash"]] for item in items if item["text_hash"] in vectors_by_hash], dtype=np.float32)
    kept = [item for item in items if item["text_hash"] in vectors_by_hash]
    np.savez_compressed(INDEX_VECTORS, vectors=matrix)
    INDEX_META.write_text(json.dumps({"version": 1, "model": embedding_service.model, "dimension": int(matrix.shape[1]) if matrix.ndim == 2 and matrix.size else 0, "vectors_file": INDEX_VECTORS.name, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "items": kept}, ensure_ascii=False), encoding="utf-8")
    library["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    LIBRARY.write_text(json.dumps(library, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"processed": processed, "failed": failed, "chunks": len(kept), "total_documents": len(documents)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
