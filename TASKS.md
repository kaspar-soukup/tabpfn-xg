# Hackathon task list

This checklist turns [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) into small, reviewable steps. Tasks 1–8 are implemented and ready for review; later tasks remain pending approval.

## Working agreement

- Work on one task at a time. Get approval before starting implementation, and stop after each task for review unless a different review cadence is agreed.
- Before starting a task, confirm its concrete files, dependencies, validation command or manual check, and expected result. Split it further if it cannot be reviewed independently.
- Preserve the research pipeline's measured behavior, feature order, fit sample, and calibration. Do not tune using external evaluation outcomes.
- Read the processing and data notebooks to understand the original work. Use the referenced research scripts and frozen outputs as the migration starting point, checking discrepancies against the notebooks.
- Leave the research workspace and original university project untouched. Never copy credentials.
- Add meaningful tests with the behavior they protect. Document each completed capability, its commands, and relevant limitations in the README.
- Follow [AGENTS.md](AGENTS.md): ask about unclear requirements instead of making assumptions; keep code clean and efficient; always check compilation. Backend tests are the agent's responsibility. All frontend testing is the user's responsibility; do not write or run frontend tests.
- For UI tasks, provide manual validation steps and record frontend acceptance as pending user validation until the user confirms it.
- Record validation results and any remaining limitations here. A task is complete only when its acceptance criteria pass and the result is ready to review.

## Decisions to confirm before affected tasks

- **UI:** Streamlit is proposed for a simple Python application; this is not yet a final selection.
- **Python and dependencies:** Python 3.14 was selected by the user for Task 2. Keep model-training dependencies optional if practical; add requirements with the affected modules.
- **Demo assets:** User approved tracking model probabilities/provenance and preparing all 908 source-derived shots locally from pinned public downloads. Source-derived data stay in ignored `data/`; publication/logo and final distribution review remain Task 18.
- **Live inference:** Confirm the hosted model interface and required fit context before promising a setup command. No paid inference runs are authorized by this checklist.
- **License:** Confirm the intended project license and upstream reuse requirements before adding one.

## Task checklist

Tasks 1–8 are implemented. Tasks 9 onward remain pending approval. The sequence may be adjusted when inspection identifies a dependency; record the reason before changing it.

### 1. Review research and record provenance

- [x] Read the relevant notebooks, scripts, existing tests, and experiment manifests.
- [x] Record selected source paths and SHA-256 hashes, source match IDs, exact fit shot IDs, ordered features, model configuration, and calibration parameters in a portable manifest.
- **Acceptance:** Every selected reference exists; the recorded settings agree with the frozen experiment; identify any discrepancy before migration.
- **Validation:** Recompute hashes and compare manifest fields with the source records. Inspect structure and sizes before deciding which artifacts to copy.
- **README:** Explain where the implementation and evidence came from and link the provenance record.

### 2. Establish minimal package and test setup

- [x] Add the package scaffold, packaging configuration, supported Python declaration, and minimal test dependencies.
- **Current status:** Scaffold, editable installation, import, compilation, and test discovery verified on Python 3.14.5. Support is declared for the 3.14 release series. No third-party test dependency is needed for `unittest`.
- **Depends on:** 1.
- **Acceptance:** The package installs and imports in a fresh environment; test discovery works. Separate optional app and experiment dependencies where useful.
- **Validation:** Editable installation, import check, and test discovery using documented commands.
- **README:** Development setup and how to run tests.

### 3. Migrate event conversion and eligibility

- [x] Extract public event conversion into `src/tabpfn_xg/data.py` with explicit inputs.
- [x] Port tests for eligible shots, exclusions, unknown categories, and independence from outcomes and supplied xG.
- **Depends on:** 1–2.
- **Acceptance:** Conversion produces the expected schema and labels; target and reference xG values cannot influence predictors.
- **Validation:** Conversion tests using small event fixtures.
- **README:** Input format, eligibility rules, and data-source attribution.

### 4. Migrate the shared feature builder

- [x] Extract the ordered 50-feature schema and geometry calculations into `src/tabpfn_xg/features.py`.
- [x] Port meaningful geometry tests and add a research parity check.
- **Depends on:** 3.
- **Acceptance:** Feature names, order, values, and missing-observation behavior match the research implementation within a stated numerical tolerance.
- **Validation:** Keeper/teammate exclusion, blockers, missing observations, degenerate geometry, symmetry, and representative source parity fixtures.
- **README:** Feature groups, coordinate units, and visibility/coverage limitations.

### 5. Migrate probability checks and calibration

- [x] Extract positive-class mapping, probability validation, and frozen calibration application.
- **Depends on:** 2, 4.
- **Acceptance:** Reversed class ordering is handled correctly; invalid probabilities fail clearly; frozen calibration reproduces research outputs.
- **Validation:** Port positive-class and calibration tests, including relevant edge cases.
- **README:** What calibration does and where frozen parameters are recorded.

### 6. Migrate model construction

- [x] Add explicit frozen model configuration and small prediction interfaces in `src/tabpfn_xg/models.py`.
- **Depends on:** 5.
- **Acceptance:** Model settings agree with the manifest; importing the cached demo does not require a token or initialize hosted inference.
- **Validation:** Configuration comparison and local interface tests with a fake model; no paid requests needed.
- **README:** Cached mode, optional model dependencies, and the fit-context requirement.

### 7. Migrate sampling and evaluation

- [x] Extract sampling, metrics, and paired match-bootstrap utilities into `src/tabpfn_xg/evaluation.py`.
- **Depends on:** 2, 5.
- **Acceptance:** Sampling and evaluation preserve the research protocol and reproducibility.
- **Validation:** Port nested sampling and clustered bootstrap tests; compare reported metrics against frozen predictions.
- **README:** Match-disjoint evaluation, metric meanings, and uncertainty calculation.

### 8. Prepare portable external demo assets

- **Current status:** Implemented and validated. User approved portable model probabilities/provenance plus direct public-data downloads to build the complete local dataset, instead of redistributing source geometry/outcomes/xG.

- [x] Add a reproducible command to obtain external events from the pinned public source and join geometry to cached predictions by shot ID.
- [x] Package frozen model predictions and provenance; prepare the complete attributed demo dataset locally (user-approved distribution approach).
- **Depends on:** 3–4, 7.
- **Acceptance:** Joins are unique and complete for the selected demo shots; cached values are unchanged; a checkout does not need research-workspace paths.
- **Validation:** Shot-ID integrity, required fields, probability checks, selected match IDs, and the full evaluation count of 908 shots when preparing the evaluation dataset.
- **README:** Asset contents, preparation command, source commit, and attribution.

### 9. Make historical fit data reproducible

- [ ] Document and implement historical acquisition/conversion using recorded source IDs and splits.
- **Depends on:** 1, 3–4.
- **Acceptance:** The exact 8,000-shot fit sample and calibration context can be reconstructed without private absolute paths. Report missing public inputs explicitly if any are found.
- **Validation:** Match overlap checks, shot IDs, split roles, feature parity, and recorded input hashes where applicable.
- **README:** Historical preparation commands, expected outputs, and time/storage requirements measured during validation.

### 10. Add the frozen experiment command

- [ ] Add an explicit-path experiment entry point using the shared modules, recorded fit sample, and frozen calibration.
- **Depends on:** 6–9.
- **Acceptance:** Documented configuration reproduces the protocol; existing frozen outputs remain unchanged. Expensive inference verification is distinguished from local checks.
- **Validation:** Offline checks of feature/schema parity and cached evaluation; any new hosted run requires separately agreed scope.
- **README:** Reproduction command, prerequisites, output locations, and which results have actually been rerun.

### 11. Build the cached pitch viewer

- [ ] Build a minimal app that loads one real shot and draws the shooter, keeper, and visible defenders with a clear goal direction and legend.
- **Depends on:** 8 and UI choice.
- **Acceptance:** It launches without a token; coordinates agree with the source shot; outcomes and model probabilities are hidden initially.
- **Validation:** Agent checks compilation and backend asset integrity. User checks token-free launch, pitch positions, legend, and initially hidden probabilities/outcome using provided steps. No frontend tests.
- **README:** One launch command, pitch legend, and cached-mode label.

### 12. Add the guessing and reveal interaction

- [ ] Let visitors select a probability, reveal all three cached model probabilities, then reveal the outcome and shot geometry.
- **Depends on:** 11.
- **Acceptance:** The sequence is intuitive; percentages match cached data; the outcome stays hidden until requested. Explain that one outcome does not validate a probability.
- **Validation:** Agent checks compilation. User checks initial, guess, prediction-reveal, and outcome-reveal states, including probability endpoints, using provided steps. No frontend tests.
- **README:** Short walkthrough of the interaction.

### 13. Add next-shot navigation

- [ ] Add a next-shot control that resets the guess and reveal state.
- **Depends on:** 12.
- **Acceptance:** A new shot never inherits another shot's guess or revealed outcome; navigation handles dataset boundaries.
- **Validation:** Agent checks compilation. User checks state reset and dataset boundaries using provided steps. No frontend tests.
- **README:** Navigation behavior.

### 14. Add the results view

- [ ] Show frozen metrics, paired confidence intervals, calibration plot, sample description, and concise limitations.
- **Depends on:** 7–8, 11.
- **Acceptance:** Every displayed value matches the frozen report. Claims describe improvement over the tested CatBoost baseline; they do not claim superiority over StatsBomb or all conventional models.
- **Validation:** Agent checks compilation and backend report values against source artifacts. User checks displayed values, plot, and explanatory text using provided steps. No frontend tests.
- **README:** Findings, uncertainty, one-club sample limitation, and links to reports.

### 15. Add optional live TabPFN inference

- [ ] Configure server-side token handling and live inference through the shared feature/model/calibration path.
- [ ] Preserve cached mode when live configuration is missing or inference fails.
- **Depends on:** 6, 9, 12 and confirmation of the live interface.
- **Acceptance:** Credentials never appear in UI, tracked files, or logs; live inputs use the frozen schema and correct fit context; visitors receive a clear mode/error message.
- **Validation:** Agent checks compilation and backend fake-client tests for success, absent token, and service failure. User checks UI mode and error messages. Optional real backend inference smoke test only after agreeing its scope. No frontend tests.
- **README:** Token configuration, prerequisites, mode labels, and fallback behavior.

### 16. Review README as a visitor

- [ ] Consolidate incremental documentation into a focused guide covering purpose, setup, launch, interaction, data preparation, reproduction, results, and limitations.
- **Depends on:** 10–15.
- **Acceptance:** A newcomer can follow the cached-demo path without notebooks, local research files, or a token; advanced commands are easy to find.
- **Validation:** Agent verifies documented backend and compilation commands and marks commands needing optional credentials or a longer run. User verifies launch and UI walkthrough instructions.
- **README:** This task reviews the complete guide rather than postponing documentation until the end.

### 17. Verify a clean checkout

- [ ] Install and check compilation in an isolated environment using only distributable project files; provide clean-checkout launch instructions for the user.
- **Depends on:** 16.
- **Acceptance:** Meaningful tests pass; the guessing flow and results view work without research data or secrets; no absolute research paths are runtime dependencies.
- **Validation:** Agent checks clean installation, compilation, and the backend test suite. User launches the cached app and performs the documented demo walkthrough. No frontend tests.
- **README:** Verified Python version and exact setup/test commands.

### 18. Check distribution and licensing

- [ ] Inspect tracked files for credentials, environments, large raw pickles, and unrelated artifacts.
- [ ] Add confirmed code licensing and required upstream/data attribution.
- **Depends on:** 8–10, 17 and license choice.
- **Acceptance:** The repository has intentional distributable assets and clear source/reuse information.
- **Validation:** Tracked-file review, asset-size review, and attribution/license inspection without printing secrets.
- **README:** License, acknowledgments, and data-use references.

### 19. Prepare submission visuals

- [ ] Capture a screenshot of the finished app and record a short demo video.
- **Depends on:** 17–18.
- **Acceptance:** Visuals show the actual working interaction and accurate findings; no credentials or private files appear.
- **Validation:** User confirms the screenshot and video represent the working UI; agent checks attribution and presentation text. Agree capture/delivery details before starting. Capturing assets does not authorize frontend testing.
- **README:** Screenshot and link to the available demo video.

## Optional follow-up: edited geometry

Not part of the initial implementation. Detail and approve separate tasks only after the core demo, setup, documentation, and reporting pass review.

- Move a defender or keeper and recompute shared features and supported predictions.
- Clearly distinguish edited geometry from the original shot. Supplied StatsBomb xG applies only to the original shot.
- Keep annotations consistent with edits and explain that edits demonstrate model behavior, not causal effects.
- Agent validates compilation, backend geometry updates, and prediction inputs. User validates UI labels and reset behavior. No frontend tests.

## Completion record

For each completed task, append:

```text
Task number and name:
Changed files:
Validation commands/manual checks:
Results:
Frontend validation: Not applicable / pending user validation / confirmed by user
README updates:
Limitations or decisions needed:
Review status:
```

### Task 1 — Review research and record provenance (2026-10-06)

- **Authorization:** User explicitly requested implementation of Task 1 and documentation for subsequent agents. Scope: portable provenance, read-only verification, handoff notes, README/task updates; no pipeline migration or inference.
- **Changed files:** `provenance/research_manifest.json`, `provenance/RESEARCH_HANDOFF.md`, `scripts/verify_provenance.py`, `tests/test_provenance.py`, `README.md`, `TASKS.md`.
- **Validation commands:** `python3 scripts/verify_provenance.py --research-root /Users/kasparsoukup/Documents/_Documents/Projects/tabPFN` — passed; `python3 -m compileall -q scripts tests` — passed; `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN python3 -m unittest discover -s tests -v` — four tests passed. From research root: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_xg*.py' -v` — 14 tests passed.
- **Results:** All 76 selected references exist and hashes match; seven externally frozen hashes agree. Recorded settings, ordered schema and calibration agree across sources. Source structure/size inventory completed; no bulk research artifacts copied. A read-only pickle diagnostic confirmed model/full/split alignment, exact ordered 8,000-shot sampling and converter parity (45,185 shots, identical labels, max difference `1.4210854715202004e-14`). The standard-library verifier does not rerun sampling/conversion; that diagnostic distinction is documented.
- **Frontend validation:** Not applicable. No frontend tests or UI checks.
- **README updates:** Provenance/handoff links, explicit-root validation commands, test outcomes, source attribution and present limitations.
- **Limitations/decisions:** No frozen-behavior discrepancy found. Constructor options extend manifest SETTINGS and are separately recorded. Historical season/date/competition mapping and pinned acquisition commit remain unresolved for Task 9. UI, dependency support, distributable assets, live inference and license choices remain pending their affected tasks.
- **Review status:** Task 1 implementation and compilation complete; ready for user review. Task 2 was subsequently authorized on 2026-10-06.

### Task 2 — Establish minimal package and test setup (2026-10-06)

- **Authorization:** User requested continuation with Task 2 and documentation of findings. Scope detailed before implementation: package scaffold/configuration, setup notes, README/task updates, fresh editable install/import, discovery, and compilation.
- **Changed files:** `pyproject.toml`, `src/tabpfn_xg/__init__.py`, `.gitignore`, `provenance/TASK_2_SETUP.md`, `README.md`, `TASKS.md`, `AGENTS.md`.
- **Findings:** Existing research packaging has placeholder metadata and an outdated Python restriction. Recorded research versions are not a support policy. Existing tests/verifier need only the standard library. App and model requirements are deferred until their code is migrated; there are no runtime dependencies or speculative extras.
- **Validation commands/results (Python 3.14.5):**
  - `python3 -m venv .venv` — created a fresh environment.
  - `.venv/bin/python -m pip install -e .` — passed after approved network retry to obtain the isolated setuptools build dependency; first sandbox attempt failed to resolve PyPI.
  - From `/private/tmp`: `/Users/kasparsoukup/Documents/_Documents/Projects/tabpfn-xg/.venv/bin/python -I -c 'import tabpfn_xg; from importlib.metadata import version; print(tabpfn_xg.__file__); print(version("tabpfn-xg"))'` — passed, imported the source package via editable installation and reported `0.1.0`.
  - `.venv/bin/python -m compileall -q src scripts tests` — passed.
  - `.venv/bin/python -m unittest discover -s tests -v` — discovered four tests, all skipped as documented without a research root; this is discovery verification, not a passing source audit.
  - `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v` — all four backend tests passed.
  - `.venv/bin/python -m pip check` — passed, no broken requirements.
- **Frontend validation:** Not applicable. No frontend tests or UI checks.
- **README updates:** Fresh-environment setup, import/compilation/test commands, skipped-test explanation, dependency policy, findings link, and verified interpreter version.
- **Final decision:** User selected Python 3.14 and requested a commit after completion. `requires-python = "~=3.14.0"` permits `>=3.14,<3.15`. `AGENTS.md` records Python 3.14 and the instruction to commit completed task changes after checks and documentation.
- **Final validation:** Repeated the editable install, compilation, discovery, source-dependent backend tests, and `pip check` above after the Python declaration; results remained successful (four skips without the research root; four passes with it). From `/private/tmp`, `/Users/kasparsoukup/Documents/_Documents/Projects/tabpfn-xg/.venv/bin/python -I -c 'import tabpfn_xg; from importlib.metadata import metadata; info = metadata("tabpfn-xg"); assert info["Requires-Python"] == "~=3.14.0"; print(info["Version"], info["Requires-Python"])'` passed and reported `0.1.0 ~=3.14.0`. `git diff --check` and `git diff --cached --check` passed.
- **Limitations/decisions needed:** Verification used Python 3.14.5. No pipeline, data, model, UI, or license migration was undertaken. Future optional dependencies remain subject to their affected tasks.
- **Review status:** Task 2 implementation and compilation complete; ready for user review. Task 3 has not started. The requested commit includes the previously uncommitted Task 1 provenance work alongside Task 2.

### Task 3 — Migrate event conversion and eligibility (2026-10-06)

- **Authorization:** User requested Task 3, prior-document review, findings, tests, and a commit. Scope and files/dependencies/checks were detailed before implementation.
- **Changed files:** `src/tabpfn_xg/data.py`, `tests/test_data.py`, `tests/test_data_parity.py`, `pyproject.toml`, `provenance/TASK_3_CONVERSION.md`, `README.md`, `TASKS.md`.
- **Findings:** Original notebooks and frozen converter agree on eligibility, first opposition keeper, category encodings, 37 base predictors and labels. Preserved missing-keeper/type exclusions and kept outcome/reference xG outside predictors. Findings note records dependency decisions, validation boundary improvements, fixture corrections and Task 4 handoff.
- **Validation commands/results (Python 3.14.5; NumPy 2.5.3; pandas 2.3.3):**
  - `.venv/bin/python -m pip install -e .` — passed after approved network retry; initial sandbox attempt could not resolve PyPI for the build dependency.
  - `.venv/bin/python -m compileall -q src scripts tests` — passed.
  - `.venv/bin/python -m unittest discover -s tests -v` — 11 conversion tests passed; six source-dependent tests skipped.
  - `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v` — all 17 backend tests passed, including the four provenance checks and two full conversion parity checks.
  - `.venv/bin/python -m pip check` — passed, no broken requirements.
  - `git diff --check` and `git diff --cached --check` — passed before commit.
- **Results:** Historical conversion: 45,185 eligible of 45,719 shots, 499 type exclusions and 35 missing keepers. External: 908 eligible of 916 shots, eight type exclusions and zero missing keepers across the 34 recorded match files. Base predictors match frozen outputs at absolute tolerance `2e-14`; labels and identifiers match exactly; external supplied xG is unchanged. Existing source hashes pass. No inference or research changes.
- **Frontend validation:** Not applicable; no frontend tests or UI checks.
- **README updates:** Native JSON/flattened input usage, ordered output/metadata separation, eligibility, validation errors, coordinate conventions, source attribution, dependencies, exact validation commands/results and limitations.
- **Limitations/decisions needed:** Additional 13 geometry features remain Task 4; data downloads, model/calibration/evaluation interfaces and distribution remain later tasks. Optional parity checks require trusted local source data. No outstanding Task 3 requirement question.
- **Review status:** Task 3 implementation and compilation complete; ready for user review. Stop here; Task 4 is not started or authorized.

### Task 4 — Migrate the shared feature builder (2026-10-06)

- **Authorization:** User requested Task 4, prior-document review, findings, tests and a commit. Scope/files/dependencies/validation detailed before implementation; stop after this task for review.
- **Changed files:** `src/tabpfn_xg/features.py`, `src/tabpfn_xg/data.py` (schema comment), `tests/test_features.py`, `tests/test_features_parity.py`, `provenance/TASK_4_FEATURES.md`, `README.md`, `TASKS.md`.
- **Findings:** Preserved ordered 37+9+4 schema, exact geometric arithmetic/settings, missing/empty distinction, invalid-entry counting, strict opposition flag, keeper ID/name exclusion, inclusive triangle bounds and strict ray projection. Immutable explicit configuration replaces the source's mutable CONFIG dictionary. Full builder reuses base columns and rebuilds added geometry through an input allowlist; metadata stays separate. No new dependencies.
- **Validation commands/results (Python 3.14.5; NumPy 2.5.3; pandas 2.3.3):**
  - `.venv/bin/python -m compileall -q src scripts tests` — passed.
  - `.venv/bin/python -m unittest discover -s tests -v` — 24 portable backend tests passed; nine source-dependent tests skipped.
  - `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v` — all 33 backend tests passed, including full historical/external feature parity and all 76 provenance hashes.
  - `.venv/bin/python -m pip check` — passed, no broken requirements.
  - `git diff --check` and `git diff --cached --check` — passed before commit.
- **Results:** All 45,185 historical rows match the frozen 13-feature table; all 908 external rows match the frozen 50-feature table after alignment by unique shot ID, at absolute tolerance `2e-14`, `rtol=0`. Additional source parity covers missing/non-list/empty frames, invalid players and goal-line degeneracy. Existing conversion/provenance tests continue to pass. Research inputs, cached predictions, fit IDs, calibration and results are unchanged.
- **Frontend validation:** Not applicable; no frontend tests or UI checks.
- **README updates:** Shared builder usage, full schema/metadata separation, groups, coordinates, frozen settings, validation errors, missing observations, coverage limitations, exact commands/results and findings link.
- **Limitations/decisions needed:** Source parity requires the explicitly supplied trusted research snapshot. Models, calibration, public acquisition and distribution remain later tasks. One initial fixture incorrectly expected zero ray coverage for a goal-centre player; corrected the fixture after inspecting the frozen projection rule. No unresolved Task 4 question.
- **Review status:** Task 4 implementation and compilation complete; ready for user review. Task 5 has not started or been authorized.

### Task 5 — Migrate probability checks and calibration (2026-10-06)

- **Authorization:** User requested Task 5, review of Task 4 provenance and the task checklist, change verification and a commit. Scope/files/dependencies/validation detailed before implementation; stop after this task for review. Earlier Task 4 handoff statements about Task 5 authorization describe their earlier state.
- **Changed files:** `src/tabpfn_xg/calibration.py`, `tests/test_calibration.py`, `tests/test_calibration_parity.py`, `provenance/TASK_5_CALIBRATION.md`, `README.md`, `TASKS.md`.
- **Findings:** Preserved class-1 lookup through either binary class order, source row-sum tolerance, frozen geometry coefficients and clipping. Added actionable probability/configuration errors, validation of both class columns, and immutable explicit calibration configuration. NumPy implements logit and a stable sigmoid; no SciPy/model dependencies or calibration optimizer needed for frozen application.
- **Validation commands/results (Python 3.14.5):**
  - `.venv/bin/python -m compileall -q src scripts tests` — passed.
  - `.venv/bin/python -m unittest discover -s tests -v` — 34 portable backend tests passed; ten source-dependent tests skipped.
  - `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v` — all 44 backend tests passed, including raw-cache calibration reproduction and all 76 provenance hashes.
  - `.venv/bin/python -m pip check` — passed, no broken requirements.
  - `git diff --check` and `git diff --cached --check` — passed before commit.
- **Results:** Both 908-row raw caches match frozen CSV shot-ID order and reproduce calibrated probabilities at `atol=2e-14`, `rtol=0`. Maximum absolute differences: CatBoost `1.1102230246251565e-16`; TabPFN `1.6653345369377348e-16`. Tests cover reversed classes, malformed classes/matrices/vectors, non-finite/out-of-range/complex values, endpoints, clipping, empty batches, known distortion, monotonicity, immutable configuration and stable large-coefficient behavior. No research files, frozen parameters, fit IDs, cached outputs or model settings changed.
- **Frontend validation:** Not applicable; no frontend tests or UI checks.
- **README updates:** Probability and calibration usage, exact frozen parameters/source, historical split roles, raw-vs-calibrated distinction, commands/results and limitations. Updated current task/test counts.
- **Limitations/decisions needed:** Optional cache parity needs the trusted research snapshot. Calibration fitting, model construction, evaluation, data assets and UI remain later scope. No outstanding Task 5 question.
- **Review status:** Task 5 implementation and compilation complete; ready for user review. Task 6 has not started or been authorized.

### Task 6 — Migrate model construction (2026-10-06)

- **Authorization:** User requested Task 6, review of Task 5/calibration and this checklist, documentation, tests and a commit. Scope/files/dependencies/validation detailed before implementation; stop after Task 6 for review. Task 5's earlier Task 6 authorization statement describes its earlier handoff state.
- **Changed files:** `src/tabpfn_xg/models.py`, `tests/test_models.py`, `pyproject.toml`, `README.md`, `provenance/TASK_6_MODELS.md`, `TASKS.md`.
- **Findings:** Frozen configuration matches both main settings and extra constructor options. Model packages are imported only by explicit construction. Fit and prediction preserve input rows/features, validate schema and label alignment, reuse positive-class/probability checks, and apply explicit calibration once. Cached calibrated CSV values bypass model construction and calibration.
- **Validation commands:**
  - `.venv/bin/python -m unittest discover -s tests -p 'test_models.py' -v` — all eight new offline tests passed.
  - `.venv/bin/python -m compileall -q src scripts tests` — passed.
  - `.venv/bin/python -m unittest discover -s tests -v` — 42 passed, ten source-dependent tests skipped.
  - `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v` — all 52 passed.
  - `.venv/bin/python -m pip install --no-deps -e .` — editable build/install passed after retry with approved network access for setuptools; sandbox attempt failed DNS. Initial `--no-build-isolation --no-deps` attempt failed because local setuptools is absent.
  - `.venv/bin/python -I -c 'from importlib.metadata import metadata; import tabpfn_xg.models; m=metadata("tabpfn-xg"); print(m.get_all("Provides-Extra")); print(m.get_all("Requires-Dist"))'` — import passed; installed metadata contains `catboost==1.2.10` and `tabpfn-client==0.6.1` only in their optional extras.
  - `.venv/bin/python -m pip check` — passed, no broken requirements.
  - `git diff --check` — passed.
- **Results:** Python 3.14.5. Fake models verify constructors without fitting, exact manifest settings, token-free import with optional imports blocked, missing dependencies, unchanged aligned fit context, reversed class mapping, calibration, rejected schema/labels, empty predictions without client calls and propagated service errors. Existing feature/calibration parity and all 76 source hashes pass. No real model fitting, inference, research changes or frozen-result changes.
- **Frontend validation:** Not applicable; no frontend code or tests.
- **README updates:** Frozen settings; cached-mode boundary; recorded-version optional extras; explicit fit/raw/calibrated usage; exact historical context responsibility; checks/results and limitations.
- **Limitations/decisions needed:** Optional model installation/real client compatibility and inference were not rerun. Exact historical fit-context reconstruction and shot-ID enforcement remain Tasks 9–10; hosted credentials and UI fallback remain Task 15. No outstanding Task 6 question.
- **Review status:** Task 6 implementation and compilation complete; ready for user review. Task 7 has not started or been authorized.


### Task 7 — Migrate sampling and evaluation (2026-10-06)

- **Authorization:** User explicitly requested Task 7. Scope, files, existing dependencies and validation detailed before implementation; stop after this task for review.
- **Changed files:** `src/tabpfn_xg/evaluation.py`, `tests/test_evaluation.py`, `README.md`, `TASKS.md`.
- **Implementation:** Migrated proportional nested sampling, binary metrics and paired whole-match bootstrap with explicit seed/replicate arguments and input validation. Preserved RNG order, ties-to-even class counts, shot weighting, percentile intervals and source clipping conventions. NumPy/pandas implement metrics without adding scikit-learn or model dependencies. Source sampling/evaluation comes from `scripts/xg_tabpfn_pilot.py`; external invocation and frozen CSV/JSON outputs define parity. Notebook acquisition context remains the historical 2015/16 data.
- **Validation commands/results (Python 3.14.5):**
  - `.venv/bin/python -m compileall -q src scripts tests` — passed.
  - `.venv/bin/python -m unittest discover -s tests -p 'test_evaluation.py' -v` — eight passed, two source-dependent tests skipped.
  - `.venv/bin/python -m unittest discover -s tests -v` — 50 passed, 12 source-dependent tests skipped.
  - `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v` — all 62 passed.
  - `.venv/bin/python -m pip check` — passed, no broken requirements.
  - `git diff --check` — passed before commit.
- **Results:** Exact ordered 8,000 fit shot IDs reproduced; four historical roles verified match-disjoint. All metrics for three models on 908 shots/34 matches and both paired bootstrap comparisons reproduce frozen outputs at `atol=2e-14`, `rtol=0`. Portable tests cover nesting, prevalence/rounding, reproducibility, pool boundaries, tied AUC, endpoints, single-class AUC, identical models, unequal cluster sizes, difference direction, singleton match intervals and malformed inputs. All 76 research hashes remain unchanged.
- **Frontend validation:** Not applicable; no frontend code or tests.
- **README updates:** Utility usage, positional alignment, sampling protocol, historical split roles, metric meanings, paired uncertainty, clipping distinctions, evidence limitations, exact commands and results.
- **Limitations/decisions needed:** Source parity requires the trusted research snapshot and reads a local pickle. Split reconstruction, portable assets and experiment CLI remain Tasks 8–10. No live/paid inference, model fitting, external tuning or new dependencies. No outstanding Task 7 questions.
- **Review status:** Task 7 implementation and compilation complete; ready for user review. Task 8 has not started or been authorized.


### Task 8 — Prepare portable external demo assets (2026-10-06)

- **Authorization:** User requested Task 8 and explicitly approved tracking model predictions/provenance while downloading StatsBomb data directly and building all 908 shots locally in ignored `data/`. Scope/files/dependencies/checks described before coding. No inference or frontend work.
- **Changed files:** `src/tabpfn_xg/assets.py`, `scripts/prepare_data.py`, `tests/test_assets.py`, `tests/test_assets_parity.py`, `assets/external/model_predictions.csv`, `assets/external/source_manifest.json`, `assets/external/README.md`, `README.md`, `TASKS.md`.
- **Implementation:** Explicit-path pinned downloader with SHA-256 verification, offline cache reuse, shared conversion/features, strict unique/complete shot-ID joins, exact float64 probability preservation, population/digest verification and deterministic local dataset output. Differing existing output is preserved. The portable CSV projects only `id,catboost,tabpfn` from the frozen cache, retaining original decimal strings and order. The source manifest records original/cache hashes and a canonical full-table digest. No new runtime dependencies or model calls.
- **Distribution decision:** The pinned StatsBomb agreement contains source-data redistribution restrictions (§1.2.1 and §7). User approved local reconstruction rather than committing source-derived geometry/outcomes/xG. StatsBomb attribution and upstream agreement/media links are included. Publication/logo and project-license review remain Task 18. This resolves the earlier full-versus-subset question: every eligible external shot is prepared locally.
- **Validation commands/results (Python 3.14.5):**
  - `.venv/bin/python -m compileall -q src scripts tests` — passed.
  - `.venv/bin/python -m unittest discover -s tests -p 'test_assets.py' -v` — nine portable asset tests passed.
  - `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -p 'test_assets_parity.py' -v` — complete bundled-cache/source parity passed.
  - `.venv/bin/python -m unittest discover -s tests -v` — 59 passed, 13 source-dependent skips.
  - `TABPFN_RESEARCH_ROOT=/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN .venv/bin/python -m unittest discover -s tests -v` — all 72 passed.
  - `.venv/bin/python -m pip check` and `git diff --check` — passed.
  - `.venv/bin/python scripts/prepare_data.py --source-manifest assets/external/source_manifest.json --predictions assets/external/model_predictions.csv --cache-dir data/external-cache --output data/external-demo --offline` — passed, producing 908 shots / 34 matches / 102 goals.
  - Real network validation before final packaging used `.venv/bin/python scripts/prepare_data.py --source-manifest /private/tmp/tabpfn-task8-source.json --predictions /Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_external_bundesliga_2023_24/evaluation_predictions.csv --cache-dir data/external-cache --output data/external-download-check` — initial sandbox DNS failure; approved retry downloaded and verified all 35 pinned public files (119,286,882 bytes). Repeated with `--offline` — identical output.
  - Isolated-copy verification copied `src/`, the preparation script, `assets/` and the public cache into a temporary directory, removed `TABPFN_RESEARCH_ROOT`/`TABPFN_TOKEN`, and used `PYTHONPATH=<temporary>/src` with the same portable CLI arguments above. Imported module path verified inside that copy; byte-identical output in 1.53 seconds. Initial path assertion was corrected to resolve macOS temporary-directory aliases. Existing installed NumPy/pandas were reused; this is not the Task 17 fresh-environment check.
  - `git check-ignore data/external-cache/matches.json data/external-demo/shots.json` — both remain ignored.
- **Results:** 908 unique shots, 34 selected matches, 102 goals; both model probabilities, source xG, outcomes and row order agree exactly with the frozen full cache. All 50 features agree within `2e-14` absolute tolerance. Portable tests protect provenance/cache integrity, download hashes, offline behavior, ID joins, source mismatches, deterministic output and refusal to overwrite drift. The source-dependent asset test validates every row/feature. All 76 research hashes remain unchanged.
- **Asset sizes:** Tracked model CSV 70,219 bytes; source manifest 5,500 bytes. Generated local `shots.json` 3,431,925 bytes; `manifest.json` 5,374 bytes. Raw downloads remain ignored.
- **README updates:** Complete research-independent preparation command, offline usage, cache recovery, schema/loading example, float precision, source attribution, measured sizes, isolated validation and limitations. Asset README describes the exact projection and digest.
- **Frontend validation:** Not applicable; no frontend code or tests.
- **Limitations/decisions needed:** First preparation needs public network access or a previously verified cache; generated source data are local assets, not granted redistribution rights. Checkout assets are not wheel package data. Historical fit reconstruction, UI, publication/logo and fresh-environment verification remain their later tasks. No outstanding Task 8 question.
- **Review status:** Task 8 implementation and compilation complete; ready for user review. Task 9 has not started or been authorized.
