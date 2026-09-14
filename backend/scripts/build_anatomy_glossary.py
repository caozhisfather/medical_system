"""Build the English to Chinese anatomical glossary for the 3D atlas.

The BodyParts3D atlas names structures in English, while the indexed teaching
material is Chinese. Without a bilingual bridge, clicking a structure cannot be
traced back to a textbook chapter or page, which is the core promise of the
virtual anatomy lab.

This script translates every distinct structure name once, using the
OpenAI-compatible endpoint from ``.env``, and caches the result in
``data/anatomy_term_glossary.json`` so later runs are offline and free.

Usage
-----
    conda activate pytorch_env
    python backend/scripts/build_anatomy_glossary.py
    python backend/scripts/build_anatomy_glossary.py --batch 30 --dry-run
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.services.anatomy_term_service import anatomy_term_service  # noqa: E402


def atlas_names(atlas_path: pathlib.Path) -> list[str]:
    manifest = json.loads(atlas_path.read_text(encoding="utf-8"))
    names: list[str] = []
    seen: set[str] = set()
    for part in manifest.get("parts", []):
        name = str(part.get("name") or "").strip()
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=20, help="names per request")
    parser.add_argument("--limit", type=int, default=0, help="stop after N names (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="report coverage without calling the API")
    args = parser.parse_args()

    root = pathlib.Path(__file__).resolve().parents[2]
    atlas_path = root / "frontend" / "public" / "anatomy" / "atlas.json"
    if not atlas_path.exists():
        raise SystemExit(f"atlas not found: {atlas_path}\nrun prepare_anatomy_models.py first")

    names = atlas_names(atlas_path)
    pending = anatomy_term_service.missing(names)
    print(f"structures={len(names)} translated={len(names) - len(pending)} pending={len(pending)}")

    if args.limit:
        pending = pending[: args.limit]

    if args.dry_run:
        for name in pending[:20]:
            print("  pending:", name)
        return

    if not pending:
        print("glossary already complete")
        return

    if not anatomy_term_service.configured():
        raise SystemExit("LLM is not configured; set OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL")

    total_added = 0
    for start in range(0, len(pending), args.batch):
        window = pending[start : start + args.batch]
        result = anatomy_term_service.translate(window)
        added = anatomy_term_service.add(result)
        total_added += added
        done = start + len(window)
        print(f"  [{done}/{len(pending)}] translated={added} cache={len(anatomy_term_service._map)}")
        if added:
            anatomy_term_service.save()

    anatomy_term_service.save()
    remaining = anatomy_term_service.missing(names)
    print(f"added={total_added} cached={len(anatomy_term_service._map)} remaining={len(remaining)}")
    print(f"written to {anatomy_term_service.__class__.__module__} cache")


if __name__ == "__main__":
    main()
