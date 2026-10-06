# TabPFN xG

Hackathon project in preparation: explore football scoring chances with TabPFN-3.5, compare predictions, and test your football intuition.

Tasks 1–5 (research review, package setup, event conversion, the shared 50-feature builder, and probability checks/calibration) are implemented and ready for review. Models and the application remain later tasks. See the [implementation plan](IMPLEMENTATION_PLAN.md) and [task checklist](TASKS.md).

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

Installation downloads setuptools for the isolated build and the NumPy/pandas runtime dependencies used by conversion. Tests use standard-library `unittest`. Discovery runs 34 portable backend tests; ten additional parity/provenance tests skip without the research snapshot. Run the source-dependent command below to validate them. No app or experiment extras are available yet; their dependencies will be added alongside the migrated capabilities. See the [Task 2 findings](provenance/TASK_2_SETUP.md). Older Python versions have not been checked.

The implementation will come from the original acquisition/processing notebooks and the frozen geometry/external research pipeline. The [portable provenance manifest](provenance/research_manifest.json) records 76 source hashes, exact ordered 8,000 fit shot IDs, historical/external match IDs, ordered 50 features, model settings and calibration. The [research handoff](provenance/RESEARCH_HANDOFF.md) explains migration pitfalls, artifact sizes, verification results and unresolved historical acquisition metadata.

Verify the selected research snapshot with standard-library Python, replacing the path if the snapshot has moved:

```sh
python3 scripts/verify_provenance.py --research-root /path/to/tabPFN
python3 -m compileall -q scripts tests
TABPFN_RESEARCH_ROOT=/path/to/tabPFN python3 -m unittest discover -s tests -v
```

These checks passed against the recorded local snapshot; four provenance tests and all 14 existing research backend tests passed. Without `TABPFN_RESEARCH_ROOT`, source-dependent tests skip. The verifier reads references only, performs no inference and needs no token. A clean checkout contains the provenance record, but not the research data; portable data preparation and demo assets are later tasks.

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
frozen order. Model interfaces are a later task.

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
