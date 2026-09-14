# Anatomy model attribution

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
