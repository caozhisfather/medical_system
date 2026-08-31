from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_RE = re.compile(r"第[一二三四五六七八九十百0-9]+章[\s　]*(.+)?")


def clean_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def main() -> int:
    parser = argparse.ArgumentParser(description="提取系统解剖学教材文本并建立页码索引")
    parser.add_argument("--source", default=r"C:\Users\lenovo\Downloads\06. 系统解剖学（第10版）.pdf")
    parser.add_argument("--output", default=str(ROOT / "data" / "anatomy_textbook.json"))
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        raise FileNotFoundError(f"教材文件不存在：{source}")

    pages: list[dict[str, object]] = []
    current_chapter = ""
    with pdfplumber.open(source) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = clean_text(page.extract_text() or "")
            chapter_match = CHAPTER_RE.search(text[:80])
            if chapter_match:
                current_chapter = f"第{chapter_match.group(0).split('章')[0].lstrip('第')}章"
                if chapter_match.group(1):
                    current_chapter = chapter_match.group(0).strip()
            pages.append({"page": index, "chapter": current_chapter, "text": text[:6000]})

    payload = {
        "source": "《系统解剖学》（第10版），主审：丁文龙，主编：崔慧先、刘学政",
        "version": 10,
        "page_count": len(pages),
        "pages": pages,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    text_pages = sum(1 for item in pages if item["text"])
    print(f"extracted_pages={len(pages)} with_text={text_pages}")
    print("output=", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
