"""Build the organ layer that sits between a system and its fine structures.

BodyParts3D ships an FMA concept graph: each concept lists the meshes that make
it up. That is exactly the ``organ -> fine structure`` relationship the viewer
needs, but the graph is deep and partly tissue-level ("segment of bronchial
tree"), so the teaching-worthy organs are selected explicitly here.

Output: ``frontend/public/anatomy/organs.json``

Usage
-----
    conda activate pytorch_env
    python backend/scripts/build_anatomy_organs.py
"""

from __future__ import annotations

import json
import pathlib

# teaching system -> organs. Each organ unions one or more FMA concepts; a part
# is kept when it survived the earlier model filtering.
ORGANS: dict[str, list[dict]] = {
    "locomotor": [
        {"id": "skull", "name": "颅骨", "nameEn": "Skull", "concepts": ["skull", "neurocranium", "viscerocranium"]},
        {"id": "vertebral-column", "name": "脊柱", "nameEn": "Vertebral column", "concepts": ["vertebral column", "vertebra"]},
        {"id": "thorax", "name": "胸廓", "nameEn": "Thoracic cage", "concepts": ["rib", "sternum"]},
        {"id": "upper-limb", "name": "上肢骨", "nameEn": "Bones of upper limb", "concepts": ["bone of upper limb"]},
        {"id": "lower-limb", "name": "下肢骨", "nameEn": "Bones of lower limb", "concepts": ["bone of lower limb"]},
        {"id": "pelvis", "name": "骨盆", "nameEn": "Pelvis", "concepts": ["pelvis"]},
    ],
    "circulatory": [
        {"id": "heart", "name": "心脏", "nameEn": "Heart", "concepts": ["heart"]},
        {"id": "aorta", "name": "主动脉", "nameEn": "Aorta", "concepts": ["aorta", "ascending aorta", "arch of aorta", "descending aorta", "abdominal aorta"]},
        {"id": "pulmonary-vessels", "name": "肺动脉与肺静脉", "nameEn": "Pulmonary vessels", "concepts": ["pulmonary trunk", "pulmonary artery", "pulmonary vein"]},
        {"id": "vena-cava", "name": "上腔静脉与下腔静脉", "nameEn": "Venae cavae", "concepts": ["superior vena cava", "inferior vena cava"]},
    ],
    "respiratory": [
        {"id": "trachea", "name": "气管", "nameEn": "Trachea", "concepts": ["trachea"]},
        {"id": "right-lung", "name": "右肺", "nameEn": "Right lung", "concepts": ["right lung"]},
        {"id": "left-lung", "name": "左肺", "nameEn": "Left lung", "concepts": ["left lung"]},
        {"id": "right-bronchial-tree", "name": "右主支气管及分支", "nameEn": "Right bronchial tree", "concepts": ["right bronchial tree"]},
        {"id": "left-bronchial-tree", "name": "左主支气管及分支", "nameEn": "Left bronchial tree", "concepts": ["left bronchial tree"]},
    ],
    "digestive": [
        {"id": "esophagus", "name": "食管", "nameEn": "Esophagus", "concepts": ["esophagus"]},
        {"id": "stomach", "name": "胃", "nameEn": "Stomach", "concepts": ["stomach"]},
        {"id": "duodenum", "name": "十二指肠", "nameEn": "Duodenum", "concepts": ["duodenum"]},
        {"id": "jejunum", "name": "空肠", "nameEn": "Jejunum", "concepts": ["jejunum", "zone of jejunum"]},
        {"id": "ileum", "name": "回肠", "nameEn": "Ileum", "concepts": ["ileum", "zone of ileum"]},
        {"id": "colon", "name": "结肠", "nameEn": "Colon", "concepts": ["cecum", "ascending colon", "transverse colon", "descending colon"]},
        {"id": "rectum", "name": "直肠", "nameEn": "Rectum", "concepts": ["rectum"]},
        {"id": "appendix", "name": "阑尾", "nameEn": "Appendix", "concepts": ["appendix"]},
        {"id": "liver", "name": "肝", "nameEn": "Liver", "concepts": ["liver"]},
        {"id": "gallbladder", "name": "胆囊", "nameEn": "Gallbladder", "concepts": ["gallbladder"]},
        {"id": "pancreas", "name": "胰腺", "nameEn": "Pancreas", "concepts": ["pancreas"]},
    ],
    "urinary": [
        {"id": "right-kidney", "name": "右肾", "nameEn": "Right kidney", "concepts": ["right kidney"]},
        {"id": "left-kidney", "name": "左肾", "nameEn": "Left kidney", "concepts": ["left kidney"]},
        {"id": "right-ureter", "name": "右输尿管", "nameEn": "Right ureter", "concepts": ["right ureter"]},
        {"id": "left-ureter", "name": "左输尿管", "nameEn": "Left ureter", "concepts": ["left ureter"]},
        {"id": "bladder", "name": "膀胱", "nameEn": "Urinary bladder", "concepts": ["urinary bladder"]},
        {"id": "urethra", "name": "尿道", "nameEn": "Urethra", "concepts": ["urethra"]},
    ],
    "reproductive": [
        {"id": "right-testis", "name": "右睾丸", "nameEn": "Right testis", "concepts": ["right testis"]},
        {"id": "left-testis", "name": "左睾丸", "nameEn": "Left testis", "concepts": ["left testis"]},
        {"id": "right-epididymis", "name": "右附睾", "nameEn": "Right epididymis", "concepts": ["right epididymis"]},
        {"id": "left-epididymis", "name": "左附睾", "nameEn": "Left epididymis", "concepts": ["left epididymis"]},
        {"id": "ductus-deferens", "name": "输精管", "nameEn": "Deferent duct", "concepts": ["right deferent duct", "left deferent duct"]},
        {"id": "seminal-vesicle", "name": "精囊", "nameEn": "Seminal vesicle", "concepts": ["seminal vesicle"]},
        {"id": "prostate", "name": "前列腺", "nameEn": "Prostate", "concepts": ["prostate"]},
    ],
    "nervous": [
        {"id": "telencephalon", "name": "端脑", "nameEn": "Telencephalon", "concepts": ["telencephalon"]},
        {"id": "diencephalon", "name": "间脑", "nameEn": "Diencephalon", "concepts": ["diencephalon"]},
        {"id": "cerebellum", "name": "小脑", "nameEn": "Cerebellum", "concepts": ["cerebellum"]},
        {"id": "midbrain", "name": "中脑", "nameEn": "Midbrain", "concepts": ["midbrain"]},
        {"id": "pons", "name": "脑桥", "nameEn": "Pons", "concepts": ["pons"]},
        {"id": "medulla", "name": "延髓", "nameEn": "Medulla oblongata", "concepts": ["medulla oblongata"]},
    ],
    "endocrine": [
        {"id": "pituitary", "name": "垂体", "nameEn": "Pituitary gland", "concepts": ["pituitary gland"]},
        {"id": "pineal", "name": "松果体", "nameEn": "Pineal body", "concepts": ["pineal body"]},
        {"id": "adrenal", "name": "肾上腺", "nameEn": "Adrenal gland", "concepts": ["right adrenal gland", "left adrenal gland"]},
    ],
    "lymphatic": [
        {"id": "thymus", "name": "胸腺", "nameEn": "Thymus", "concepts": ["thymus", "lobe of thymus"]},
        {"id": "spleen", "name": "脾", "nameEn": "Spleen", "concepts": ["spleen"]},
    ],
}


def main() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    atlas_path = root / "frontend" / "public" / "anatomy" / "atlas.json"
    if not atlas_path.exists():
        raise SystemExit(f"atlas not found: {atlas_path}")

    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    kept_parts = {part["id"] for part in atlas["parts"]}
    concept_elements = {c["name"].lower(): c["elements"] for c in atlas["concepts"]}

    systems = []
    for system_id, definition in ORGANS.items():
        organs = []
        for organ in definition:
            part_ids: list[str] = []
            seen: set[str] = set()
            for concept_name in organ["concepts"]:
                for element in concept_elements.get(concept_name.lower(), []):
                    if element in kept_parts and element not in seen:
                        seen.add(element)
                        part_ids.append(element)
            if not part_ids:
                print(f"  skip {system_id}/{organ['id']}: no parts matched")
                continue
            organs.append(
                {
                    "id": organ["id"],
                    "name": organ["name"],
                    "nameEn": organ["nameEn"],
                    "system": system_id,
                    "partIds": part_ids,
                }
            )
        if organs:
            systems.append({"system": system_id, "organs": organs})
        print(f"  {system_id:14s} organs={len(organs)}")

    payload = {
        "source": "BodyParts3D 4.0 FMA concepts, curated into teaching organs",
        "systems": systems,
    }
    out = root / "frontend" / "public" / "anatomy" / "organs.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    total = sum(len(entry["organs"]) for entry in systems)
    print(f"organs={total} written to {out}")


if __name__ == "__main__":
    main()
