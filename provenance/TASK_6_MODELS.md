# Task 6 model construction findings

Reviewed 2026-10-06. User authorized Task 6, review of Task 5/calibration and the
task checklist, documentation, validation and a commit. Scope is frozen
construction and small model interfaces; live setup and inference remain later
tasks. Task 5's earlier authorization statements describe its handoff state.

Read `AGENTS.md`, `TASKS.md`, `IMPLEMENTATION_PLAN.md`, `README.md`,
`RESEARCH_HANDOFF.md`, `TASK_5_CALIBRATION.md`, the portable manifest, the current
calibration/feature code and tests. Reviewed the pilot constructors and the
external experiment's fit/prediction/calibration path. Revisited acquisition
notebook source cells; the processing notebook contains no model construction
or fit/prediction path. The frozen scripts, not the legacy university app,
define the settings for this migration.

## Preserved configuration and boundaries

`models.py` uses frozen dataclasses for each model's constructor parameters.
CatBoost settings include all five main settings and the three recorded extra
options. TabPFN includes model `v3.5_default`, four estimators, seed 123, no
thinking mode, `fit_preprocessors`, and automatic inference precision. These
are checked against `external_experiment.settings` plus
`model_constructor_options`. No tuning, new variant, sampling or calibration
fitting was introduced. Construction accepts only `catboost` or `tabpfn`;
unknown names fail before a client is loaded.

Optional packages load inside `make_model` only when explicitly called without
an injected factory. Missing packages report the matching install extra;
internal import errors are not disguised as missing top-level packages.
Importing the module and validating cached probabilities require no optional
package or token and initialize no hosted service. A fresh-interpreter test
blocks optional imports and removes `TABPFN_TOKEN` to verify this boundary.

The two extras pin recorded versions CatBoost 1.2.10 and tabpfn-client 0.6.1;
they remain absent from core runtime requirements. Editable packaging and
installed extra metadata were verified; optional installations, real constructor
compatibility and inference were not rerun. There is no live setup promise.

Fit/prediction interfaces require an exact ordered 50-column feature DataFrame
and finite real numeric values. They pass data unchanged to the model, with no
scaling, column reordering or selection. Fit validates aligned binary labels,
requires both classes, and checks Series indexes before any model call. Arrays
are positional. The caller owns shot-ID provenance and the exact ordered 8,000
historical fit context; Tasks 9–10 will reconstruct/enforce it. This layer does
not pretend schema validation verifies sample provenance.

Raw prediction reuses `positive_probability`, including reversed class order
and both-column validation. Calibrated prediction requires an explicit
`Calibration`, predicts once and applies it once. Empty queries return empty
vectors without client calls. Service errors propagate for later application
fallback. Cached evaluation CSV values already contain calibrated probabilities
and bypass this prediction/calibration path. Provider xG is never calibrated.

## Validation and handoff

Exact commands/results appear in `TASKS.md` and README. Compilation passed;
portable suite 42 passed/ten skipped; source-enabled suite all 52 passed.
The eight new tests use fake models only and cover manifest agreement, lazy
import/construction, optional dependency errors, fit alignment, class mapping,
single calibration, malformed inputs, empty queries and service failures.
Existing source-enabled tests continue to verify full feature/cache parity and
all 76 source hashes. No research files or frozen outputs changed.

The first editable-install check with `--no-build-isolation --no-deps` failed
because setuptools is absent from the local venv. The normal isolated build
then hit sandbox DNS restrictions while obtaining setuptools. Retrying
`.venv/bin/python -m pip install --no-deps -e .` with approved network access
succeeded. Installed metadata lists both optional extras and their exact pins;
`pip check` passes. Neither optional model package was installed for this task.

No frontend tests, real model fitting, paid/live inference, credential reads,
data downloads or research modifications occurred. Task 6 implementation is
ready for user review; frontend acceptance is not applicable. Task 7 remains
unimplemented and needs separate authorization.
