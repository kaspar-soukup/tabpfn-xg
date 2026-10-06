# Task 1 research handoff

Reviewed 2026-10-06. Task 1 is implemented and ready for user review; Task 2 is not authorized. Read this note and `research_manifest.json` before migrating code. The research workspace is a reference, not an application runtime dependency.

The manifest records 76 selected files with relative source paths, SHA-256 hashes and byte sizes; CSV columns/row counts; the ordered 50-feature schema; the exact ordered 8,000 fit shot IDs; all 1,823 historical eligible match IDs grouped by role; the 34 external matches; the pinned public commit; model settings and extra constructor options; calibration; metrics; and paired differences. Research HEAD is `11cb8723984c85b57828935cad4fd95e2525ba2d`, branch `xg-tabpfn`. Some sources/results are uncommitted or ignored, so a checkout of HEAD is insufficient.

All seven hashes embedded in the external manifest match current working-tree bytes. Geometry and pilot records agree with the external freeze. No mismatch in the frozen feature order, settings, calibration or exact ordered fit sample was found. The reviewed notebooks were read as source cells, not executed.

## Migration findings

| Later task | Source and behavior to preserve |
| --- | --- |
| 2: setup | Research runs Python 3.14 and records package versions in `historical.pilot_manifest.versions`. These are observed versions, not a chosen support policy. The Task 1 verifier uses only the standard library. Do not inherit placeholder packaging requirements. |
| 3: conversion | `scripts/xg_external_data.py` reproduces `Processing.ipynb` feature derivation. Keep only Open Play / Free Kick with the first observed opposition goalkeeper (`position.name == Goalkeeper`, `teammate is False`). Categories are explicitly validated. Feet combine into one column; absent flags become zero. Label is Goal=1, all recognized other outcomes=0. Provider xG stays outside predictors. |
| 4: features | `xg_tabpfn_pilot.FEATURES` supplies 37 columns; append nine `PRESSURE_FEATURES`, then four `GEOMETRY_FEATURES`. Preserve that order, including left/right post naming. Coordinates are 120×80; goal centre `(120,40)`, posts `(120,36)` / `(120,44)`; angles are radians and distances are coordinate units. |
| 4: geometry | `scripts/xg_features.py`: radii 0.6 / 0.9, 101 goalface samples, distance sentinel `hypot(120,80)`. Missing frame and empty frame differ. Teammates and keepers are excluded from defender counts; keeper detection accepts position ID 1 or name. Invalid entries are counted before teammate filtering. Coverage requires projection strictly inside a ray segment; triangle inclusion has tolerance `1e-10`. Keep degenerate geometry behavior and finite values. |
| 5: calibration | Use geometry selection, not the pilot's original 37-feature calibration. Both geometry models use calibrated probabilities: CatBoost `[1.0123564537857361, 0.08384092826439743]`, TabPFN `[1.023112240680613, 0.070507598294854]`. Apply sigmoid(a×logit(clipped p)+b), clip `1e-7`; do not refit. Positive probability must map through `classes_`, not assume column 1. |
| 6: models | Settings alone omit constructor options. Preserve CatBoost `verbose=False`, `allow_writing_files=False`, `thread_count=4`; TabPFN seed 123, `fit_mode='fit_preprocessors'`, `inference_precision='auto'`, `thinking_mode=False`, model `v3.5_default`, four estimators. These are recorded in the portable manifest. No hosted calls were made during Task 1. |
| 7: sampling/evaluation | First reconstruct the original stratified 75/25 row split (seed 123), then split matches within original training rows into 60/15/10/15 roles. Sort match IDs before RNG permutation and sort role row positions. Original-test rows remain excluded even if their matches occur in a role. Do not replace this with grouping all historical rows. Sample proportionally within classes using seed 123, then shuffle; preserve exact fit order. Bootstrap is paired, whole-match, shot-weighted, 2,000 replicates, seed 123; uncertainty is conditional on fitted models. |
| 8: demo assets | Cached predictions have columns `id,match_id,outcome,catboost,tabpfn,statsbomb`. Join geometry by unique `id`. External `features.csv` contains 50 feature columns and no IDs: its row order follows predictions, so validate that alignment before use. Raw event JSON supplies freeze frames and source geometry. |
| 9: historical context | `Getting_data.ipynb` requests 2015/16 competitions excluding Champions League, season ID 27, through statsbombpy. Saved raw data contain 45,719 shots; conversion excludes 499 shot types and 35 missing-keeper shots, leaving 45,185 eligible shots / 1,823 matches. No pinned historical acquisition commit or date/competition mapping is in the reviewed records. Notebook intent does not verify the season of every saved row. Exact saved match IDs and hashes are authoritative for reconstruction; resolve public metadata and missing inputs in Task 9. |
| 10: experiments | Refactor mutable `pilot.OUT` and implicit research roots into explicit paths. Do not call research `load_data()` for a read-only audit: it creates directories and can write manifests/splits. External script resolves master only when `source.json` is absent; the new reproduction path must use the already frozen commit. |
| 11 onward: UI | Existing research `app.py` is a legacy UI reference, not the prediction path. Use the migrated shared features/model/calibration. UI choice, assets/distribution, live interface and licensing decisions remain pending. |

## Evidence and artifact decisions

External source commit: `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`, StatsBomb Open Data competition 9 / season 281. The 34 available matches are Bayer Leverkusen's Bundesliga 2023/24 fixtures, both teams' shots, rather than a complete league schedule. Audit: 916 shots, eight excluded penalties, zero missing keepers, 908 eligible shots, 102 goals; no historical match or shot overlap. Observed freeze frames have no missing frames or invalid player entries.

The external report is the main evidence. TabPFN improves log loss by 2.54% and Brier by 3.20% against the tested equal-data CatBoost baseline, with both paired intervals excluding zero. StatsBomb has better point estimates and both difference intervals include zero. The earlier geometry report uses previously examined evaluation matches and is exploratory. Do not turn it into a superiority claim over StatsBomb. Shot annotations and freeze frames do not establish complete tracking or live feature availability.

Sizes were inspected before copying. Selected source artifacts total 335,285,986 bytes. Only the provenance record was copied/derived into this repository; scripts, notebooks, pickles, predictions, figures and event JSON remain in research. This keeps Task 1 separate from pipeline and asset migration.

| Artifact | Bytes | Structure / later use |
| --- | ---: | --- |
| Raw historical pickle | 83,931,003 | 45,719 × 26; historical conversion input |
| Historical full pickle | 108,454,596 | 45,185 × 61; IDs, source fields, freeze frames and features |
| Historical model pickle | 14,100,036 | 45,185 × 38; 37 features + target |
| Historical splits CSV | 2,686,226 | 45,185 rows; position, shot_id, match_id, role |
| Historical geometry CSV | 5,347,924 | 45,185 × 13; positional alignment to processed rows |
| External predictions CSV | 89,657 | 908 × 6; calibrated model probabilities and supplied xG |
| External features CSV | 308,607 | 908 × 50; no shot IDs |
| External CatBoost / TabPFN NPZ | 31,937 / 29,128 | Raw probability caches; preserve separately from calibrated CSV |
| External events | About 120 MB total | 34 JSON files; per-file sizes and hashes in manifest |

Practical candidates for Task 8 are the compact prediction/report assets plus selected real-shot geometry. Do not copy the large historical pickles as public demo dependencies. Distribution and upstream reuse/attribution must be confirmed in their assigned tasks. The source inventory excludes credentials, `.env` and environment contents.

## Validation record and commands

From this repository:

```sh
python3 scripts/verify_provenance.py --research-root /Users/kasparsoukup/Documents/_Documents/Projects/tabPFN
python3 -m compileall -q scripts tests
TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN python3 -m unittest discover -s tests -v
```

Results: verifier passed all 76 hashes and frozen-record checks; compilation passed; all four provenance backend tests passed (including rejection of missing files, corrupted hashes, and altered feature order/fit IDs/calibration). The verifier is read-only, accepts an explicit root, does not load pickles/import research code, and performs no network or model calls. Tests require the selected snapshot; without `TABPFN_RESEARCH_ROOT` they are skipped, not evidence of a passing source audit. An arbitrary future research tree may fail hashes intentionally; investigate drift rather than regenerating the record to hide it.

From the research root, the existing backend tests were rerun:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_xg*.py' -v
```

Result: all 14 source backend tests passed. This does not imply the pipeline has been migrated or a clean installation has been verified. No frontend checks were written or run.

Additional read-only diagnostic used the research Python environment to load the three trusted local pickles, compare model/full indexes and columns against the split CSV, call `sample_rows` on fit-role positions, and call `convert_shots` on raw data. It reproduced the exact ordered 8,000 IDs; all 45,185 converted labels matched and maximum absolute feature difference was `1.4210854715202004e-14`. These observations are stored under `verification` in the manifest. The standard-library verifier checks exact recorded fit IDs against the frozen manifest and fit membership; it does not independently rerun NumPy sampling or pickle conversion.

No model fitting, hosted inference, external downloads, or frozen-result changes occurred. Next agent should await approval for Task 2 and detail that task's files, dependencies and checks before starting. User review of Task 1 remains pending.
