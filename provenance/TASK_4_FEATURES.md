# Task 4 shared-feature findings

Reviewed 2026-10-06. The user authorized implementation of Task 4, findings,
backend validation and a commit. Earlier notes saying Task 4 was unauthorized
refer to their earlier sessions. Scope is shared predictors only.

## References reviewed

Read all previous project markdowns: `AGENTS.md`, `IMPLEMENTATION_PLAN.md`,
`TASKS.md`, `README.md`, research handoff, Task 2 setup and Task 3 conversion
notes. Reviewed the portable manifest, research `scripts/xg_features.py`, its
five geometry tests and `docs/xg_features.md`; inspected geometry/external
experiment assembly and acquisition/processing notebook source cells without
executing notebooks.

The processing notebook defines the original 37 features, coordinates, post
naming, keeper selection and angle. The later research geometry script adds
nine pressure and four coverage features. External experiment assembly appends
those 13 to the original ordered base columns. No discrepancy was found.

## Implementation decisions and preserved behavior

- Reuse `data.BASE_FEATURES`; `features.FEATURES` is exactly that tuple plus
  `PRESSURE_FEATURES` plus `GEOMETRY_FEATURES`. No duplicated base schema.
- `build_features` returns all 50 predictor columns; `build_geometry_features`
  corresponds to the research function that returns only the additional 13.
  `shot_features` supports a single converted row. Preserve input row/index
  order, including repeated index labels, and leave the input unchanged.
- Reuse converted base columns; geometry reads only shooter/keeper coordinates
  and freeze frames. Outcomes, reference xG and other metadata are ignored.
  Pre-existing geometry columns are rebuilt, preventing stale values after edits.
- Replace mutable module CONFIG with an immutable `GeometryConfig` argument.
  Defaults preserve radii 0.6/0.9, 101 goalface rays and `hypot(120,80)` sentinel.
  Frozen reproduction uses the defaults. No retuning or model runs occurred.
- Preserve the source's NumPy arithmetic, segment denominator floor `1e-12`,
  triangle determinant threshold/tolerance `1e-10`, inclusive 2/5-unit counts,
  and strict interior ray projections. Coverage overlap is counted once.
- Frame availability is `isinstance(frame, list)`; an empty list is available.
  Invalid player entries/locations count before team/keeper exclusion. Only
  `teammate is False` counts an opponent. Keepers are excluded by position ID 1
  or name, while the converter's notebook-derived keeper selection requires name.
- No observed defenders gives sentinel nearest distances and zero defender
  counts/coverage; keeper coverage still uses the selected keeper.
  Degenerate triangles count zero blockers. Features remain finite on the goal
  line. Visibility is incomplete and circle/ray coverage is an approximation.
- Add actionable boundary errors for missing/duplicate columns, invalid
  shot/keeper coordinates, non-finite predictors and malformed position mappings.
  The research code raised an AttributeError for a nonempty non-mapping position;
  migration raises ValueError. Valid frozen rows and invalid-location counting
  retain source behavior. Empty tables with required columns return the schema.
- NumPy/pandas dependencies already added by Task 3 suffice. No changes to
  package requirements, research files, original university project or credentials.

## Validation and handoff

Ported the five source geometry cases and expanded boundaries, opposition flag,
keeper name/ID, invalid observations, reflection, coverage union, geometry input
validation, schema/order, index preservation, input immutability, metadata
independence, configuration validation and empty-table checks.

Three optional read-only parity tests use `TABPFN_RESEARCH_ROOT`: historical
45,185-row geometry table, external 908-row full 50-feature table aligned by
unique shot ID, and synthetic missing/invalid/degenerate fixtures against the
source function. CSV comparison tolerance is `atol=2e-14`, `rtol=0`; frozen
column order and row counts are exact. Historical CSV alignment follows the
recorded processed-pickle row positions. External alignment follows prediction
IDs, matching the experiment's positional feature CSV convention.

The initial endpoint fixture expected a goal-centre player to cover no ray.
That is false for off-centre goalface rays: its centre can project inside their
segments. Corrected the fixture without changing production geometry. The
centre shooting-line distance still excludes both endpoints. This subtlety
should be retained in future geometry explanations and editing features.

Exact final commands and results are in Task 4's completion record in `TASKS.md`
and README: compilation passed, portable suite 24 passed/nine skipped, full
source-enabled suite all 33 passed, dependency and diff checks passed. Provenance
tests still verify all 76 source hashes. Tested Python 3.14.5, NumPy 2.5.3,
pandas 2.3.3. No frontend tests, fitting or paid/live inference.

Task 5 can consume the 50-column builder for probability/calibration interfaces
once authorized. No calibration, model construction, sampling, evaluation,
asset preparation, downloads or UI was implemented in Task 4.
