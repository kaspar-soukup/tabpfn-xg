# Task 3 conversion findings

Reviewed 2026-10-06; authorized by the user's request to continue Task 3,
document findings, test, and commit. Scope: event conversion/eligibility only.

## References and findings

Read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `TASKS.md`, `README.md`,
`RESEARCH_HANDOFF.md`, `TASK_2_SETUP.md`, and the recorded provenance manifest.
Inspected research `scripts/xg_external_data.py`, its four conversion tests,
`xg_tabpfn_pilot.py` for the original ordered 37 predictors, the external
experiment's acquisition paths, and source cells in `Processing.ipynb` and
`Getting_data.ipynb` without executing the notebooks.

- The frozen converter reproduces notebook eligibility, keeper selection,
  distances, angles, one-hot categories, combined feet, missing flags, and labels.
  Unlike the later defender geometry, conversion requires keeper **name**, not
  position ID. The first qualifying keeper is authoritative, even if a later
  entry has a location and the first does not. No keeper location is an exclusion.
- Exclude unsupported shot types before checking the frame or eligible categories.
  Unknown eligible body part, technique, play pattern, or outcome must fail.
- Freeze frames are retained for Task 4. Predictors contain no outcome/reference
  xG; both remain separate output metadata.
- `BASE_FEATURES` holds the original ordered 37 names in `data.py`. Task 4 should
  reuse this tuple when appending the nine pressure and four geometry predictors;
  do not duplicate or reorder it. Task 3 does not implement those 13 features.
- Research imports the entire pilot just for feature names, introducing unrelated
  dependencies. The migrated module imports only NumPy/pandas and math, accepts
  explicit inputs, and has no research paths, downloads, filesystem side effects,
  model initialization, or UI dependency.
- Required-field, identifier, duplicate-ID, finite/range, and flag validation uses
  actionable `ValueError` errors rather than production assertions. These reject
  malformed inputs without changing valid frozen conversion. StatsBomb reference
  probabilities remain untouched; probability checks belong to later tasks.

## Dependency and validation decisions

Use `numpy>=2.4,<3` and `pandas>=2.3.3,<3` as required conversion dependencies,
retaining the research pandas major series and Python 3.14 support. Verified
installation resolved NumPy 2.5.3 and pandas 2.3.3, matching the inspected research
environment. Broad version ranges are not proof of numerical parity for every
possible future resolver result; the recorded tested versions are authoritative.

Tests port the four original behavioral cases (the unknown-category case is
expanded to all three category families), and cover every recognized category
and outcome, free kicks, strict first-keeper selection, exclusion precedence,
empty/non-shot inputs, missing flags/frames, invalid locations, required fields,
and duplicate IDs. Schema order is checked against the portable frozen manifest.
Two optional read-only parity tests align external predictions by shot ID and
compare notebook-produced historical rows. They require the explicitly supplied
research root; the default suite needs no private data or token.

Successful checks and commands are recorded in the Task 3 completion record in
`TASKS.md`. Final parity: 45,185 historical shots (499 type exclusions, 35 missing
keepers), 908 external shots (eight excluded penalties, no missing keepers),
37 base predictors within absolute tolerance `2e-14`, identical IDs/match IDs and
labels, unchanged external supplied xG. All 76 provenance hashes still pass.

During validation, a fixture initially expected an error for a keeper with no
location; it was corrected to the frozen missing-keeper exclusion. The external
parity fixture initially pointed to a nonexistent `events/` subdirectory; it now
uses the actual event paths recorded in the manifest. No production behavior was
changed to accommodate either fixture issue.

No research files, frozen outputs, or credentials were modified/copied. There
are no frontend changes or tests. Data acquisition, 50-feature geometry, model
interfaces/calibration, historical reconstruction, and distributable assets stay
in their assigned later tasks. Task 3 is ready for user review; Task 4 requires
its own authorization.
