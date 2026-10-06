# TabPFN xG

Hackathon project in preparation: explore football scoring chances with TabPFN-3.5, compare predictions, and test your football intuition.

Tasks 1 (research review), 2 (package setup), and 3 (event conversion) are implemented and ready for review. The shared 50-feature builder, models, and application remain later tasks. See the [implementation plan](IMPLEMENTATION_PLAN.md) and [task checklist](TASKS.md).

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

Installation downloads setuptools for the isolated build and the NumPy/pandas runtime dependencies used by conversion. Tests use standard-library `unittest`. Discovery runs 11 portable conversion tests; six additional parity/provenance tests skip without the research snapshot. Run the source-dependent command below to validate them. No app or experiment extras are available yet; their dependencies will be added alongside the migrated capabilities. See the [Task 2 findings](provenance/TASK_2_SETUP.md). Older Python versions have not been checked.

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
distances use coordinate units and angles use radians. The additional 13
pressure/coverage predictors belong to Task 4; this output is not yet ready for
50-feature model inference.

Flattened inputs need the fields listed in `data.RAW_COLUMNS`; the four flag
columns may be omitted. Non-shot native events are ignored. Missing required
fields, unknown eligible categories/outcomes, duplicate eligible shot IDs,
missing eligible identifiers, malformed frame players, and invalid observed
shot/keeper coordinates raise actionable errors. Reference xG is carried through
unchanged; probability validation is a later capability.

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
