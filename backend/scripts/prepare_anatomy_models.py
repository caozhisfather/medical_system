"""Prepare the open-license BodyParts3D atlas used by the virtual anatomy lab.

Provenance
----------
BodyParts3D 4.0, (c) The Database Center for Life Science, licensed under
CC Attribution 4.0 International. The published source contains 2,234 OBJ
meshes; the binary packing reused here comes from the MIT-licensed
``ashemag/human-atlas`` project, which converts axes/units, simplifies
geometry, quantizes normals to signed 16-bit, and packs each mesh into a
shared chunk with byte offsets recorded in ``atlas.json``.

This script downloads the published chunks, keeps the organ systems plus the
skeleton, repacks them into smaller chunks, and writes the result to
``frontend/public/anatomy`` together with an attribution notice.

Usage
-----
    conda activate pytorch_env
    python backend/scripts/prepare_anatomy_models.py
"""

from __future__ import annotations

import json
import pathlib
import urllib.request

RAW_BASE = "https://raw.githubusercontent.com/ashemag/human-atlas/main/public/models/"

# The outer layers add ~25 MB and hide everything underneath in a whole-body
# view, so muscle, skin, connective tissue, and the sensory organs are skipped.
# Every system taught in a systematic anatomy course is kept.
EXCLUDE_SYSTEMS = {"muscular", "sensory", "integumentary", "connective"}

# The upstream grouping files the brain's ventricular system under "cardiac".
# That stretches the heart's bounding box up into the skull, so focusing the
# heart framed the whole trunk and barely zoomed. Reassign those meshes.
SYSTEM_OVERRIDES = {
    "FJ1730": "nervous",  # third ventricle
    "FJ1731": "nervous",  # fourth ventricle
    "FJ1752": "nervous",  # interventricular foramen
    "FJ1767": "nervous",  # left lateral ventricle
    "FJ1814": "nervous",  # right lateral ventricle
}

ATTRIBUTION = """# Anatomy model attribution

The files in this directory (`atlas.json`, `body-*.bin`) are derived from
**BodyParts3D 4.0**, (c) The Database Center for Life Science, licensed under
[CC Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

- Dataset: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- License: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- Publication: Mitsuhashi et al. (2009), *BodyParts3D: 3D structure database for
  anatomical concepts*, https://doi.org/10.1093/nar/gkn613

Binary packing and geometry optimisation follow the MIT-licensed
[`ashemag/human-atlas`](https://github.com/ashemag/human-atlas) project:
axes and units converted from millimetres/Z-up to metres/Y-up, geometry
simplified with meshoptimizer, normals quantized to signed 16-bit, and meshes
packed into shared chunks with byte offsets recorded in `atlas.json`.

## Adaptation performed here

`backend/scripts/prepare_anatomy_models.py` downloads the published chunks and
keeps the systems taught in a systematic anatomy course: `skeletal`, `cardiac`,
`arterial`, `venous`, `respiratory`, `digestive`, `urinary`, `reproductive`,
`nervous`, `endocrine`, and `lymphatic`. The outer layers (`muscular`,
`sensory`, `integumentary`, `connective`) are omitted: together they add about
25 MB and conceal the deeper structures in a whole-body view.

Two changes are applied on top of the source grouping:

- The brain's ventricular system (`FJ1730`, `FJ1731`, `FJ1752`, `FJ1767`,
  `FJ1814`) is filed under `cardiac` upstream. That stretched the heart's
  bounding box up into the skull, so those meshes are reassigned to `nervous`.
- Meshes are re-packed one chunk per system, letting the viewer fetch only the
  systems it is about to draw.

Positions, normals, and indices are copied unchanged; only their byte offsets
and chunk assignment are recalculated.

BodyParts3D represents an adult male reference anatomy. It is not a complete
model of every human anatomical structure or variation. This material is for
medical education and is not a clinical tool.
"""


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "medical-system-anatomy/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def section(buffer: bytes, offset: int, length: int) -> bytes:
    chunk = buffer[offset : offset + length]
    if len(chunk) != length:
        raise ValueError(f"truncated section at offset {offset}: wanted {length}, got {len(chunk)}")
    return chunk


def align(buffer: bytearray, boundary: int = 4) -> int:
    while len(buffer) % boundary:
        buffer.append(0)
    return len(buffer)


def main() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    target = root / "frontend" / "public" / "anatomy"
    target.mkdir(parents=True, exist_ok=True)

    print("fetching atlas manifest ...")
    manifest = json.loads(fetch(RAW_BASE + "atlas.json"))

    selected: list[dict] = []
    for part in manifest["parts"]:
        system = SYSTEM_OVERRIDES.get(part["id"], part["system"])
        if system in EXCLUDE_SYSTEMS:
            continue
        selected.append({**part, "system": system})
    if not selected:
        raise SystemExit("no parts matched the system filter")

    needed_chunks = sorted({part["chunk"] for part in selected})
    print(f"parts={len(selected)} source-chunks={len(needed_chunks)}")

    raw: dict[int, bytes] = {}
    for index in needed_chunks:
        name = f"body-{index}.bin"
        print(f"  downloading {name} ...")
        raw[index] = fetch(RAW_BASE + name)

    packed: list[bytes] = []
    chunk_systems: list[str] = []
    new_parts: list[dict] = []

    grouped: dict[str, list[dict]] = {}
    for part in selected:
        grouped.setdefault(part["system"], []).append(part)

    # One chunk per system keeps the payload splittable, so the viewer can fetch
    # just the systems it is about to draw instead of the whole atlas.
    for system_id in sorted(grouped):
        current = bytearray()
        for part in grouped[system_id]:
            source = raw[part["chunk"]]
            position_bytes = section(source, part["positions"], part["vertexCount"] * 3 * 4)
            normal_bytes = section(source, part["normals"], part["vertexCount"] * 3 * 2)
            index_bytes = section(source, part["indices"], part["indexCount"] * 4)

            offset_positions = align(current)
            current += position_bytes
            offset_normals = align(current, 2)
            current += normal_bytes
            offset_indices = align(current)
            current += index_bytes

            new_parts.append(
                {
                    "id": part["id"],
                    "name": part["name"],
                    "conceptId": part["conceptId"],
                    "system": system_id,
                    "chunk": len(packed),
                    "positions": offset_positions,
                    "normals": offset_normals,
                    "indices": offset_indices,
                    "vertexCount": part["vertexCount"],
                    "indexCount": part["indexCount"],
                    "bounds": part["bounds"],
                }
            )

        packed.append(bytes(current))
        chunk_systems.append(system_id)
        print(f"  packed {system_id:14s} parts={len(grouped[system_id]):4d} bytes={len(current)/1024/1024:.2f} MB")

    part_ids = {part["id"] for part in new_parts}
    concepts = []
    for concept in manifest["concepts"]:
        elements = [element for element in concept["elements"] if element in part_ids]
        if elements:
            concepts.append({"id": concept["id"], "name": concept["name"], "elements": elements})

    output_manifest = {
        "version": manifest.get("version"),
        "sex": manifest.get("sex"),
        "source": manifest.get("source"),
        "scope": "Organ systems and skeleton, extracted from the full BodyParts3D atlas.",
        "parts": new_parts,
        "concepts": concepts,
        "chunks": [
            {"url": f"/anatomy/body-{index}.bin", "bytes": len(payload), "system": chunk_systems[index]}
            for index, payload in enumerate(packed)
        ],
        "triangles": sum(part["indexCount"] // 3 for part in new_parts),
    }

    for stale in target.glob("body-*.bin"):
        stale.unlink()

    for index, payload in enumerate(packed):
        (target / f"body-{index}.bin").write_bytes(payload)
    (target / "atlas.json").write_text(
        json.dumps(output_manifest, separators=(",", ":")), encoding="utf-8"
    )
    (target / "ATTRIBUTION.md").write_text(ATTRIBUTION, encoding="utf-8")

    total = sum(len(payload) for payload in packed)
    print(f"parts={len(new_parts)} concepts={len(concepts)} chunks={len(packed)}")
    print(f"written to {target}  ({total / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
