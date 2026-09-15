from __future__ import annotations

from pathlib import Path

import win32com.client


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\lenovo\Downloads\内科规培技能问诊总结.doc")
OUTPUT = ROOT / "data" / "history_taking_standard.txt"


def main() -> int:
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        document = word.Documents.Open(str(SOURCE), ReadOnly=True, AddToRecentFiles=False, Visible=False)
        try:
            text = (document.Content.Text or "").strip()
        finally:
            document.Close(False)
    finally:
        word.Quit()

    OUTPUT.write_text(text, encoding="utf-8")
    print(f"chars={len(text)}")
    print(text[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
