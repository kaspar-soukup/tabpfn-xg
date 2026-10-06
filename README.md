# TabPFN xG

Hackathon project in preparation: explore football scoring chances with TabPFN-3.5, compare predictions, and test your football intuition.

Tasks 1–8 (research review, package setup, event conversion, the shared 50-feature builder, probability checks/calibration, model construction/interfaces, sampling/evaluation, and portable demo preparation) are implemented and ready for review. The application remains a later task. See the [implementation plan](IMPLEMENTATION_PLAN.md) and [task checklist](TASKS.md).

The supported Python release series is 3.14 (`>=3.14,<3.15`). Development setup was verified in a fresh virtual environment with Python 3.14.5:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -I -c 'import tabpfn_xg; from importlib.metadata import version; print(version("tabpfn-xg"))'
python -m compileall -q src scripts tests
python -m unittest discover -s tests -v
python -m pip check
```

Installation downloads setuptools for the isolated build and the NumPy/pandas runtime dependencies used by conversion. Tests use standard-library `unittest`. Discovery runs 59 portable backend tests; thirteen additional parity/provenance tests skip without the research snapshot. Run the source-dependent command below to validate them. Optional model extras are described below; no app extra is available yet. See the [Task 2 findings](provenance/TASK_2_SETUP.md). Older Python versions have not been checked.

The implementation will come from the original acquisition/processing notebooks and the frozen geometry/external research pipeline. The [portable provenance manifest](provenance/research_manifest.json) records 76 source hashes, exact ordered 8,000 fit shot IDs, historical/external match IDs, ordered 50 features, model settings and calibration. The [research handoff](provenance/RESEARCH_HANDOFF.md) explains migration pitfalls, artifact sizes, verification results and unresolved historical acquisition metadata.

Verify the selected research snapshot with standard-library Python, replacing the path if the snapshot has moved:

```sh
python3 scripts/verify_provenance.py --research-root /path/to/tabPFN
python3 -m compileall -q scripts tests
TABPFN_RESEARCH_ROOT=/path/to/tabPFN python3 -m unittest discover -s tests -v
```

These checks passed against the recorded local snapshot; four provenance tests and all 14 existing research backend tests passed. Without `TABPFN_RESEARCH_ROOT`, source-dependent tests skip. The verifier reads references only, performs no inference and needs no token. A clean checkout contains provenance and frozen model predictions. The external demo preparation command below obtains source data directly; historical research data are not included.

Frozen external evidence covers 908 eligible shots from 34 Bayer Leverkusen Bundesliga 2023/24 fixtures (both teams). TabPFN improves on the tested equal-data CatBoost baseline; it does not establish superiority over StatsBomb or all xG models. Source data originate from StatsBomb Open Data; the manifest pins commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. Distribution/licensing and historical public-input reconstruction remain pending. No app launch command is available yet.

## Event conversion

The [converter](src/tabpfn_xg/data.py) accepts parsed native StatsBomb event JSON
and an explicit match ID, or an already flattened shot DataFrame. It performs no
network access and requires no token. For a local native event file:

```python
import json
from pathlib import Path
from tabpfn_xg.data import BASE_FEATURES, flatten_events, convert_shots

# Use the match ID associated with this file.
match_id = 3895052
events = json.loads(Path(f"{match_id}.json").read_text())
shots, audit = convert_shots(flatten_events(events, match_id))
x = shots[list(BASE_FEATURES)]
y = shots["shot_outcome_encoded"]
reference_xg = shots["shot_statsbomb_xg"]
print(audit)
```

Only Open Play and Free Kick shots with an observed opposition goalkeeper are
eligible. Keeper selection preserves the original notebook rule: first frame
entry with `position.name == "Goalkeeper"` and `teammate is False`. Missing
frames, absent keepers, or a selected keeper without a location are excluded.
Other shot types are excluded first. No eligible shots raises `ValueError`.

Output has 37 ordered base predictors followed by `id`, `match_id`,
`shot_freeze_frame`, `shot_outcome_encoded`, and `shot_statsbomb_xg`.
The supplied xG and outcome are metadata, never predictors. Goal maps to 1;
the seven recognized other outcomes map to 0. Feet share one category, and
missing boolean flags become zero. Coordinates use the StatsBomb 120×80 pitch;
distances use coordinate units and angles use radians. Pass this output to
`features.build_features` to append the 13 pressure/coverage predictors in the
frozen order. Pass that feature table to the model interfaces described below.

Flattened inputs need the fields listed in `data.RAW_COLUMNS`; the four flag
columns may be omitted. Non-shot native events are ignored. Missing required
fields, unknown eligible categories/outcomes, duplicate eligible shot IDs,
missing eligible identifiers, malformed frame players, and invalid observed
shot/keeper coordinates raise actionable errors. Reference xG is carried through
unchanged; use `calibration.probability_check` before consuming it as a probability.

Source events and the original acquisition notebooks use
[StatsBomb Open Data](https://github.com/hudl/open-data). Preserve StatsBomb
attribution and consult the upstream data-use terms before distributing data.
Task 3 distributes code and synthetic test fixtures only; downloads and portable
demo assets remain later tasks. See [Task 3 findings](provenance/TASK_3_CONVERSION.md).

Task 3 validation on Python 3.14.5, NumPy 2.5.3, pandas 2.3.3:

```sh
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python -m unittest discover -s tests -v
TABPFN_RESEARCH_ROOT=/path/to/tabPFN .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
```

Compilation and dependency checks passed. Portable discovery: 11 passed, six
skipped. With the recorded research root: all 17 passed, including conversion
parity for 45,185 historical and 908 external shots at absolute tolerance
`2e-14`, identical labels/IDs, and unchanged external reference xG. Source checks
read trusted local pickles and JSON only; never load an untrusted pickle. No
model fitting, inference, or frontend testing was performed.

## Shared feature builder

The [shared builder](src/tabpfn_xg/features.py) uses converted shots from the
example above:

```python
from tabpfn_xg.features import FEATURES, build_features, build_geometry_features

x = build_features(shots)  # Exactly 50 columns; metadata stays in shots.
assert tuple(x.columns) == FEATURES
extra = build_geometry_features(shots)  # Just the 13 added predictors.
```

Both builders preserve row order and index, including repeated index labels.
`FEATURES` reuses the converter's 37 `BASE_FEATURES`, then appends nine
`PRESSURE_FEATURES` and four `GEOMETRY_FEATURES`. Base values are reused;
geometry is rebuilt from shooter coordinates, keeper coordinates and the freeze
frame. Outcomes, provider xG, shot-end coordinates and extra input columns cannot
influence the added features. Missing/duplicate required columns, non-finite
predictors and invalid shot/keeper coordinates raise `ValueError`. Empty input
with the required columns returns an empty table with the ordered schema.

| Group | Predictors |
| --- | --- |
| Base (37) | Original flags, categorical indicators, shooter/keeper positions, distances and shot angle |
| Pressure (9) | Visible defender count/presence, missing frame and invalid-player counts, nearest defender distance, counts within 2/5 units and the goal triangle, nearest defender to the shooting line |
| Coverage (4) | Defender and keeper goal coverage, unobstructed goal fraction, keeper offset from the shooter–goal-centre segment |

Coordinates use a 120×80 pitch with goal centre `(120,40)` and posts `(120,36)`
and `(120,44)`. Distances are coordinate units, not metres; base angles are
radians. The immutable default `GeometryConfig` preserves defender radius 0.6,
keeper radius 0.9, 101 evenly spaced goalface samples, and the pitch-diagonal
missing-distance sentinel `hypot(120,80)` (about 144.22). Use these defaults for
frozen-model reproduction; no settings were tuned during migration.

Only visible opposition outfield players with valid locations count as
defenders. Keeper detection here accepts position ID 1 **or** name
`Goalkeeper`; conversion's original keeper selection still requires the name.
Invalid player entries/locations are counted before filtering teammates. A
missing/non-list frame differs from an empty list; both have no observed
defenders. No observed defenders gives zero defender counts/coverage and sentinel
defender distances; keeper coverage still uses the selected keeper. Degenerate goal-line triangles count zero blockers and remain finite.
Triangle boundaries are included with tolerance `1e-10`.

Coverage is the fraction of rays whose segment has a player centre projected
strictly between its endpoints and within the fixed radius. Overlap is counted
once for the unobstructed fraction. A player at goal centre may still project
inside a ray aimed at another goalface point. Freeze frames show visible players,
not complete tracking: zero observed blockers does not establish an empty
defence. Coverage approximates circles in a plane; it omits height, stance,
movement and ball trajectory.

Task 4 validation on Python 3.14.5, NumPy 2.5.3 and pandas 2.3.3:

```sh
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python -m unittest discover -s tests -v
TABPFN_RESEARCH_ROOT=/path/to/tabPFN .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
```

Compilation and dependency checks passed. Portable suite: 24 passed, nine
skipped; with the recorded research snapshot, all 33 backend tests passed.
All 45,185 historical geometry rows and all 908 external rows with 50 predictors
match the frozen CSVs at absolute tolerance `2e-14` (`rtol=0`). Additional source
parity fixtures verify missing, invalid and degenerate observations; provenance
checks confirm all 76 source hashes are unchanged. These optional checks read
trusted local research data; they are not a public-data preparation command.
No model fitting, inference or frontend checks were performed. See the
[Task 4 findings](provenance/TASK_4_FEATURES.md).

## Probability checks and frozen calibration

The [calibration module](src/tabpfn_xg/calibration.py) validates probability
vectors and maps goal probabilities through a binary model's `classes_`.
`positive_probability(model, x)` calls `predict_proba(x)`, requires exactly
classes 0 and 1 in either order, and validates both columns, shape and row sums.
It does not construct or fit a model. `probability_check(p, n)` requires a
one-dimensional vector of exactly `n` finite values in `[0,1]`; endpoints and
empty batches are valid. Invalid inputs raise `ValueError` with the failed
requirement. Row sums preserve the research tolerance (`rtol=1e-5`, `atol=1e-8`).

For raw probabilities already obtained from the frozen geometry models:

```python
from tabpfn_xg.calibration import (
    CATBOOST_CALIBRATION, TABPFN_CALIBRATION,
    apply_calibration, probability_check,
)

raw_tabpfn = probability_check([0.1, 0.5, 0.9], 3)
calibrated_tabpfn = apply_calibration(raw_tabpfn, TABPFN_CALIBRATION)
calibrated_catboost = apply_calibration([0.1, 0.5, 0.9], CATBOOST_CALIBRATION)
```

Calibration adjusts probabilities using
`sigmoid(a * logit(clip(p, 1e-7, 1 - 1e-7)) + b)`. The immutable
`Calibration` configuration contains `a`, `b` and `clip`. Frozen CatBoost
parameters are `[1.0123564537857361, 0.08384092826439743]`; TabPFN parameters
are `[1.023112240680613, 0.070507598294854]`. They are recorded in
`external_experiment.frozen_selection` in the
[manifest](provenance/research_manifest.json), from
`results/xg_geometry/selection.json`. They were learned on separate historical
calibration matches and selected on historical validation matches before the
external test. No refitting is implemented. Calibration cannot guarantee
accuracy for one shot or a new population.

Apply calibration once to raw model probabilities. The external raw NPZ caches
contain uncalibrated values; `evaluation_predictions.csv` already contains
calibrated CatBoost/TabPFN values. Do not calibrate that CSV again or apply these
model-specific parameters to the supplied StatsBomb xG.

Task 5 validation on Python 3.14.5:

```sh
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python -m unittest discover -s tests -v
TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
git diff --check
```

Compilation, dependency and diff checks passed. Portable suite: 34 passed,
ten source-dependent tests skipped. With the recorded research snapshot: all
44 backend tests passed. Applying the frozen parameters to each model's 908 raw
cached probabilities reproduces its external CSV values within `2e-14` absolute
tolerance (`rtol=0`); measured maximum differences are `1.11e-16` for CatBoost
and `1.67e-16` for TabPFN. Cache shot IDs match CSV row order exactly, and all
76 provenance hashes remain unchanged. Source-dependent checks are read-only;
there were no frontend checks, model fitting or paid/live inference. No new
dependencies were added. See [Task 5 findings](provenance/TASK_5_CALIBRATION.md).

## Frozen model interfaces

The [model module](src/tabpfn_xg/models.py) exposes immutable `CATBOOST_CONFIG`
and `TABPFN_CONFIG`, matching the manifest's settings and constructor options.
CatBoost uses depth 4, 200 iterations, learning rate 0.1, L2 penalty 10, seed
123, four threads, no verbose output and no file writing. TabPFN uses
`v3.5_default`, four estimators, seed 123, `thinking_mode=False`,
`fit_mode='fit_preprocessors'` and `inference_precision='auto'`.

Importing this module needs neither a token nor either optional model package.
Cached mode uses the previously calibrated CSV predictions and
`calibration.probability_check`; it never constructs/fits a model or recalibrates
those values. Portable external preparation is described below; the cached application remains a later task.

Optional extras pin the model package versions recorded in the research
manifest. Install only the extra needed for explicit model work:

```sh
python -m pip install -e '.[catboost]'  # catboost==1.2.10
python -m pip install -e '.[tabpfn]'    # tabpfn-client==0.6.1
```

These optional installations and real client construction/inference have not
been rerun in this repository. This task checks the interfaces with fake models;
it does not provide token setup or authorize paid requests. Optional live
inference remains Task 15.

For a caller with an explicitly prepared fit context and query table:

```python
from tabpfn_xg.models import make_model, fit_model, predict_raw, predict_calibrated
from tabpfn_xg.calibration import CATBOOST_CALIBRATION

# fit_x: exact ordered 8,000 historical fit shots, 50 FEATURES columns.
# fit_y: aligned binary outcomes; query_x: the same ordered feature schema.
model = make_model("catboost")  # Explicit construction; does not fit.
fit_model(model, fit_x, fit_y)
raw = predict_raw(model, query_x)
calibrated = predict_calibrated(model, query_x, CATBOOST_CALIBRATION)
```

`predict_calibrated` makes its own prediction and calibrates it once. To reuse
`raw` without another prediction, use `apply_calibration(raw, CATBOOST_CALIBRATION)`.
For TabPFN, use `make_model('tabpfn')` and `TABPFN_CALIBRATION`; real hosted
fit/predict calls may incur charges. Construction is lazy, not a cached-mode
operation. `make_model(..., factory=...)` accepts an offline constructor for tests.

Fit and query inputs must be DataFrames containing exactly `FEATURES` in order,
with finite real numeric values. Fit requires both binary classes, aligned
one-dimensional labels, and an identical index when labels are a Series.
Rows, index and labels are passed unchanged; there is no resampling or scaling.
Empty query batches return empty probabilities without calling the model.
Probability/class validation reuses Task 5; service errors propagate to the
caller, with application fallback deferred to Task 15.

The caller must supply the exact ordered 8,000-shot context recorded in
`external_experiment.fit_shot_ids`, including its historical outcomes and
50-feature geometry. Configuration alone cannot reproduce predictions.
`fit_model` checks input schema and labels, not shot-ID provenance; historical
context reconstruction and enforcement in the experiment command remain Tasks
9–10. Frozen calibration is already supplied and must not be refitted on queries.

Task 6 validation on Python 3.14.5:

```sh
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -I -c 'from importlib.metadata import metadata; import tabpfn_xg.models; m=metadata("tabpfn-xg"); print(m.get_all("Provides-Extra")); print(m.get_all("Requires-Dist"))'
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python -m unittest discover -s tests -v
TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
git diff --check
```

Editable build/install, metadata import, compilation, dependency and diff checks
passed. Portable suite: 42 passed, ten skipped; source-enabled suite: all 52
passed, including unchanged frozen cache calibration, feature parity and all
76 source hashes. Eight new offline tests cover constructor settings, lazy
imports without a token, dependency errors, aligned fit inputs, reversed class
mapping, calibration, rejected inputs, empty batches and service failures.
No real model fitting/inference or frontend checks were performed. See
[Task 6 findings](provenance/TASK_6_MODELS.md).


## Sampling and evaluation

The [evaluation module](src/tabpfn_xg/evaluation.py) provides offline utilities
using the existing NumPy/pandas dependencies:

```python
from tabpfn_xg.evaluation import sample_rows, metrics, clustered_difference

# fit_positions contains only positions assigned to the historical fit role.
selected = sample_rows(fit_positions, historical_labels, seed=123, size=8000)
scores = metrics(outcomes, tabpfn_probabilities)
comparison = clustered_difference(
    outcomes, tabpfn_probabilities, catboost_probabilities, match_ids,
)
```

Sampling preserves the source algorithm: permute each class with NumPy's seeded
random generator, take class counts proportional to pool prevalence using
Python's ties-to-even rounding, then shuffle the combined sample. For the same
pool and seed, smaller samples have nested membership; their output order is
not a prefix of larger samples. Positions must be unique and in bounds. Sizes
from zero through the pool size are accepted. The exact ordered frozen sample
uses seed 123 and 8,000 shots; merely matching its prevalence is insufficient.

Historical fit, calibration, validation and evaluation roles are match-disjoint.
The research first reserved the original shot-level test subset, then assigned
matches from the remaining rows to those four roles. The original test subset
is not another match-disjoint role. This module samples an already assigned fit
pool; it does not recreate or change splits. Historical reconstruction remains
Task 9. The external test uses 908 shots (102 goals) from 34 previously unseen
Bayer Leverkusen Bundesliga 2023/24 fixtures, including both teams. Model and
calibration choices were frozen before that evaluation.

`metrics` returns log loss (penalizes confident errors), Brier score (mean squared
probability error), ROC AUC (ranking with half credit for ties), predicted and
observed goal rates, shot count and goal count. Lower log loss/Brier and higher
AUC are better. Inputs must be aligned, nonempty binary labels and finite
probabilities in `[0,1]`; alignment is positional, so join by shot ID first.
Single-class samples return NaN AUC. Log loss clips at float64 machine epsilon;
Brier and AUC use the original probabilities.

`clustered_difference` returns log-loss and Brier differences **first model minus
second model** and percentile 95% intervals. Negative differences favor the
first model. Defaults reproduce 2,000 bootstrap replicates with seed 123, drawing
34 whole matches with replacement for the external sample, using identical draws
for both models and metrics. Every shot in a selected match is included, repeated
matches contribute repeatedly, and the resulting means are weighted by shots,
not equally by match. Intervals use NumPy's linear 2.5%/97.5% quantiles. Match IDs
must be aligned, nonmissing and sortable. Explicit `seed` and `replicates`
arguments support other analyses; keep defaults for frozen reproduction.

The research bootstrap clips probabilities at `1e-15` for log loss and carries
those clipped values into its Brier differences. This endpoint behavior is
preserved; aggregate `metrics` retains its separate source conventions.
Intervals quantify match-resampling uncertainty, not training uncertainty or
transportability to other leagues. Frozen intervals favor TabPFN over the tested
CatBoost baseline for both losses; intervals versus StatsBomb include zero.
StatsBomb has better point estimates. This one-club sample does not establish
superiority over StatsBomb or all conventional models.

Task 7 validation on Python 3.14.5:

```sh
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python -m unittest discover -s tests -p 'test_evaluation.py' -v
.venv/bin/python -m unittest discover -s tests -v
TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
git diff --check
```

Compilation and dependency checks passed. Evaluation-only discovery: eight
passed, two source-dependent tests skipped. Full portable suite: 50 passed,
12 skipped. With the recorded research snapshot: all 62 backend tests passed.
The ordered 8,000 fit IDs match exactly; all three external models' metrics and
both paired comparisons' estimates/intervals match frozen outputs at absolute
tolerance `2e-14` (`rtol=0`). All 76 source hashes remain unchanged. Optional
sampling parity reads a trusted local pickle; never load untrusted pickles.
No research data are distributed by this task, and no model fitting, inference
or frontend checks were performed.


## External demo assets

The [portable inputs](assets/external/README.md) contain 908 shot IDs with frozen,
already calibrated CatBoost/TabPFN predictions (70,219 bytes) and a source
manifest (5,500 bytes). The user approved downloading StatsBomb data directly
and generating the complete dataset locally in ignored `data/`. Source geometry,
outcomes and supplied StatsBomb xG are not committed. These are checkout assets;
run the following from the repository root after the editable installation.

```sh
.venv/bin/python scripts/prepare_data.py \
  --source-manifest assets/external/source_manifest.json \
  --predictions assets/external/model_predictions.csv \
  --cache-dir data/external-cache \
  --output data/external-demo
```

The first run downloads about 119.3 MB (34 match event files plus metadata) from
StatsBomb commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`, competition 9,
season 281. No research paths, historical data, optional model packages, token or
inference are needed. Add `--offline` to require the existing verified cache;
later runs can reuse downloads. Conversion excludes eight penalties from 916
shots, leaving all 908 eligible shots, 102 goals and 34 matches. There is no
outcome-based demo subset selection.

The [preparation code](src/tabpfn_xg/assets.py) verifies every source/cache hash,
uses the shared conversion and feature builder, and joins by unique shot ID in
frozen prediction order. The canonical full-table digest verifies outcomes,
match IDs, supplied xG and both model probabilities exactly. Duplicate, missing
or extra IDs, invalid probabilities, changed source files or population counts
fail before output is published. Cached model values are not recomputed or
recalibrated. Corrupt cache files are not silently replaced; restore the pinned
file or remove the corrupt local cache file before retrying. Verified files from
an interrupted run remain reusable.

`data/external-demo/` contains:

- `shots.json` (3,431,925 bytes): 908 records containing `id`, `match_id`, binary
  `outcome`, `catboost`, `tabpfn`, `statsbomb`, the ordered 50 predictors, and
  `shot_freeze_frame`. All original visible frame players are retained.
- `manifest.json` (5,374 bytes): pinned source, match/event/input/output hashes,
  selected match IDs, eligibility counts, feature order and attribution. The
  source-manifest hash uses canonical compact JSON rather than its indentation.

The output directory appears only after validation. An identical rerun is
accepted; an existing differing dataset is preserved and requires a new output
path. Coordinates retain the StatsBomb 120×80 convention, attacking toward goal
centre `(120,40)`. Distances are source coordinate units, not metres. Freeze
frames describe observed players, not complete tracking.

Load the local records without sacrificing float precision:

```python
import json
from pathlib import Path
import pandas as pd
from tabpfn_xg.assets import checked_bytes
from tabpfn_xg.features import FEATURES

folder = Path("data/external-demo")
manifest = json.loads((folder / "manifest.json").read_text())
shots = pd.DataFrame(json.loads(checked_bytes(
    folder / "shots.json", manifest["shots_sha256"],
)))
features = shots[list(FEATURES)]
# shots.catboost/tabpfn are already calibrated; shots.statsbomb is supplied xG.
```

Data source: [StatsBomb Open Data](https://github.com/hudl/open-data). The pinned
[source README](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/README.md)
requests attribution and a StatsBomb logo when publishing analysis; see the
[official media pack](https://statsbomb.com/media-pack/) and
[source agreement](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf).
This task does not grant redistribution rights for the generated source-derived
data. Publication/logo and project-license review remain Task 18.

Task 8 validation on Python 3.14.5:

```sh
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python -m unittest discover -s tests -p 'test_assets.py' -v
.venv/bin/python -m unittest discover -s tests -v
TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
git diff --check
```

Compilation, dependency and diff checks passed. Nine portable asset tests passed;
the full portable suite has 59 passes and 13 source-dependent skips. All 72 tests
pass with the research snapshot. Full asset parity compares all 908 rows and
probabilities exactly, and all 50 features at `atol=2e-14`, `rtol=0`.

A real download verified all 35 source files (119,286,882 bytes), followed by an
identical offline rerun. The documented command with bundled inputs also passed
in an isolated directory containing copied project files and that public cache,
with no research paths or token configured. It imported the isolated source and
produced byte-identical output in 1.53 seconds. This used the existing Python
3.14 environment and installed NumPy/pandas; a fresh-environment release check
remains Task 17. No inference, frontend tests or research-file changes occurred.
