from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.case_library_importer import import_case_library


def main() -> int:
    parser = argparse.ArgumentParser(description="导入并脱敏内科病例知识库")
    parser.add_argument("--source", default=r"C:\Users\lenovo\Downloads\内科病例\内科病例")
    parser.add_argument("--output", default=str(ROOT / "data" / "case_knowledge_base.json"))
    parser.add_argument("--limit", type=int, default=0, help="只导入前 N 条（0 表示全部）")
    args = parser.parse_args()

    entries, report = import_case_library(args.source)
    if args.limit:
        entries = entries[: args.limit]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"version": 1, "entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"imported={report['imported']} scanned={report['scanned_files']} skipped={report['skipped']}")
    print("categories=" + json.dumps(report["categories"], ensure_ascii=False))
    if report["failures"]:
        print("failures:")
        for failure in report["failures"]:
            print(" -", failure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
