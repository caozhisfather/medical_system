"""Extract text from registered PDFs without splitting top-level documents."""
from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "data" / "document_library.json"
OUT = ROOT / "storage" / "document_ocr"
sys.path.insert(0, str(ROOT))
from backend.app.services.qwen_vision_service import qwen_vision_service  # noqa: E402


def clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> None:
    payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
    documents = payload.get("documents", [])
    OUT.mkdir(parents=True, exist_ok=True)
    processed = failed = skipped = 0
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for item in documents:
        source = Path(item.get("source_path", ""))
        if not source.exists() or source.suffix.lower() != ".pdf":
            item["ocr_status"] = "source_unavailable"
            item["processing_status"] = "原文件不可用"
            failed += 1
            continue
        target = OUT / f"{item['id']}.json"
        if target.exists() and item.get("ocr_status") == "completed":
            skipped += 1
            continue
        try:
            reader = PdfReader(str(source), strict=False)
            pages = []
            non_empty = 0
            for page_number, page in enumerate(reader.pages, start=1):
                text = clean(page.extract_text() or "")
                pages.append({"page": page_number, "text": text})
                non_empty += bool(text)
            # 扫描版 PDF 没有文本层时，渲染页面并交给 Qwen 视觉模型识别。
            if not non_empty and qwen_vision_service.configured():
                try:
                    import pypdfium2 as pdfium
                    pdf = pdfium.PdfDocument(str(source))
                    for index, page_data in enumerate(pages):
                        bitmap = pdf[index].render(scale=1.8)
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as image_file:
                            image_path = Path(image_file.name)
                        bitmap.to_pil().save(image_path)
                        try:
                            page_data["text"] = clean(qwen_vision_service.recognize_image(image_path))
                            non_empty += bool(page_data["text"])
                        finally:
                            image_path.unlink(missing_ok=True)
                    pdf.close()
                except Exception as vision_exc:
                    item["ocr_error"] = f"视觉OCR失败：{vision_exc}"[:240]
            target.write_text(json.dumps({"document_id": item["document_id"], "pages": pages}, ensure_ascii=False), encoding="utf-8")
            item["page_count"] = len(pages)
            item["ocr_text_path"] = str(target.relative_to(ROOT))
            item["ocr_status"] = "completed" if non_empty else "scanned_pdf"
            item["processing_status"] = "待脱敏" if non_empty else "需要视觉OCR"
            item["status"] = "待脱敏" if non_empty else "待OCR"
            item["updated_at"] = now
            processed += 1
            payload["updated_at"] = now
            LIBRARY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"processed {processed}: {item['title']}", flush=True)
        except Exception as exc:  # keep the batch moving for malformed PDFs
            item["ocr_status"] = "failed"
            item["processing_status"] = "OCR失败"
            item["ocr_error"] = str(exc)[:240]
            item["updated_at"] = now
            failed += 1
            payload["updated_at"] = now
            LIBRARY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"failed {failed}: {item['title']}", flush=True)
    payload["updated_at"] = now
    LIBRARY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"processed": processed, "failed": failed, "skipped": skipped, "total": len(documents)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
