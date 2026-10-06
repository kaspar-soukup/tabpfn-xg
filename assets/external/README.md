# Frozen external model cache

`model_predictions.csv` contains 908 shot IDs and the already calibrated
CatBoost/TabPFN probabilities, in the original evaluation order. It is a
column projection (`id,catboost,tabpfn`) of the research
`results/xg_external_bundesliga_2023_24/evaluation_predictions.csv`.
The original decimal strings are copied verbatim using CSV parsing; neither
predictions nor calibration are recomputed. The original file's SHA-256 is
recorded as `original_predictions_sha256` in `source_manifest.json` and in the
[research provenance](../../provenance/research_manifest.json).

`source_manifest.json` records the pinned StatsBomb commit, competition/season,
34 match IDs, source hashes, 50-feature order, expected eligibility/goal counts,
and cache integrity. Its `evaluation_predictions_digest` hashes a compact JSON
array of `[id, integer match_id, integer outcome, catboost.hex(), tabpfn.hex(),
statsbomb.hex()]` rows in frozen order, using Python float64 values. This lets
local preparation verify the full original table without distributing its
outcomes or supplied StatsBomb xG. Source hashes and selection are copied from
the research provenance; they are never resolved from a moving branch.

Build the full local dataset using the command in the
[project README](../../README.md#external-demo-assets). These files are checkout
assets, not Python wheel package data. All source events, geometry, outcomes and
supplied xG are acquired directly from StatsBomb and remain in ignored `data/`.
The tracked cache is model output; it does not contain the historical fit data.
No token, model package or inference is needed to prepare the cached dataset.

Data source: [StatsBomb Open Data](https://github.com/hudl/open-data), commit
`4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. The
[pinned source README](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/README.md)
requests StatsBomb attribution and logo use when publishing analysis. Consult
the [source agreement](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf)
and [official media pack](https://statsbomb.com/media-pack/). This project does
not relicense StatsBomb data. The user approved local preparation in place of
redistributing source-derived assets. Publication/logo and project-license
review remain Task 18; no endorsement by StatsBomb is implied.
