# Hackathon task list

This checklist turns [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) into small, reviewable steps. Tasks 1–4 are implemented and ready for review; later tasks remain pending approval.

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
- **Demo assets:** Confirm a portable, appropriately attributed way to distribute the real-shot geometry and cached predictions.
- **Live inference:** Confirm the hosted model interface and required fit context before promising a setup command. No paid inference runs are authorized by this checklist.
- **License:** Confirm the intended project license and upstream reuse requirements before adding one.

## Task checklist

Tasks 1–4 are implemented. Tasks 5 onward remain pending approval. The sequence may be adjusted when inspection identifies a dependency; record the reason before changing it.

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

- [ ] Extract positive-class mapping, probability validation, and frozen calibration application.
- **Depends on:** 2, 4.
- **Acceptance:** Reversed class ordering is handled correctly; invalid probabilities fail clearly; frozen calibration reproduces research outputs.
- **Validation:** Port positive-class and calibration tests, including relevant edge cases.
- **README:** What calibration does and where frozen parameters are recorded.

### 6. Migrate model construction

- [ ] Add explicit frozen model configuration and small prediction interfaces in `src/tabpfn_xg/models.py`.
- **Depends on:** 5.
- **Acceptance:** Model settings agree with the manifest; importing the cached demo does not require a token or initialize hosted inference.
- **Validation:** Configuration comparison and local interface tests with a fake model; no paid requests needed.
- **README:** Cached mode, optional model dependencies, and the fit-context requirement.

### 7. Migrate sampling and evaluation

- [ ] Extract sampling, metrics, and paired match-bootstrap utilities into `src/tabpfn_xg/evaluation.py`.
- **Depends on:** 2, 5.
- **Acceptance:** Sampling and evaluation preserve the research protocol and reproducibility.
- **Validation:** Port nested sampling and clustered bootstrap tests; compare reported metrics against frozen predictions.
- **README:** Match-disjoint evaluation, metric meanings, and uncertainty calculation.

### 8. Prepare portable external demo assets

- [ ] Add a reproducible command to obtain external events from the pinned public source and join geometry to cached predictions by shot ID.
- [ ] Package a practical demo dataset with provenance and attribution.
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
