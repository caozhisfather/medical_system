"""Pre-compute embeddings for the extracted anatomy textbook pages."""

import json
import sys
from pathlib import Path

import numpy as np

# Allow importing backend modules from scripts/ directory.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.config import ROOT_DIR
from backend.app.services.embedding_service import EmbeddingService


def main() -> None:
    data_dir = ROOT_DIR / "data"
    textbook_file = data_dir / "anatomy_textbook.json"
    emb_file = data_dir / "anatomy_textbook_embeddings.npy"
    meta_file = data_dir / "anatomy_textbook_embeddings.json"

    if not textbook_file.exists():
        print(f"Textbook file not found: {textbook_file}")
        raise SystemExit(1)

    payload = json.loads(textbook_file.read_text(encoding="utf-8"))
    pages = payload.get("pages", [])
    if not pages:
        print("No pages found in textbook file.")
        raise SystemExit(1)

    texts = []
    metadata = []
    for idx, page in enumerate(pages):
        text = page.get("text", "").strip()
        if not text:
            continue
        texts.append(text)
        metadata.append(
            {
                "index": idx,
                "page": page.get("page"),
                "chapter": page.get("chapter", ""),
            }
        )

    print(f"Encoding {len(texts)} pages with {EmbeddingService().model} ...")
    service = EmbeddingService()
    embeddings = service.encode(texts, batch_size=4)

    np.save(emb_file, embeddings)
    meta_file.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")

    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Saved: {emb_file}")
    print(f"Saved: {meta_file}")


if __name__ == "__main__":
    main()
