# Task 2 setup findings

Reviewed 2026-10-06. The user authorized Task 2 in this session. This note
supplements the Task 1 research handoff; its statement that Task 2 was not
authorized describes the earlier session.

## Inspected references

- `TASKS.md`, `AGENTS.md`, and `IMPLEMENTATION_PLAN.md`: Task 2 covers packaging,
  a supported Python declaration, installation/import checks, and test discovery.
  Pipeline migration and UI selection belong to later tasks.
- `provenance/RESEARCH_HANDOFF.md` and `research_manifest.json`: the research
  interpreter is Python 3.14. Recorded scientific/model package versions are
  observations of the frozen run, rather than a portable dependency policy.
- Research `pyproject.toml`: inherited `expected_goals` name, placeholder
  description, and Python `~=3.10.0` restriction. These do not describe this
  project and should not be copied.
- Research `requirements.txt`, README, and script imports: NumPy/pandas serve
  conversion and geometry; SciPy/scikit-learn serve calibration/evaluation;
  CatBoost/tabpfn-client serve model execution. The old UI also lists Streamlit,
  matplotlib, and mplsoccer. None is used by the package scaffold.
- Local `scripts/verify_provenance.py` and `tests/test_provenance.py`: standard
  library only. The four existing backend tests use `unittest`, and intentionally
  skip without `TABPFN_RESEARCH_ROOT`.

## Setup decisions

- The user selected Python 3.14. Declare `requires-python = "~=3.14.0"`
  (`>=3.14,<3.15`); broader interpreter support is not claimed.
- Use the planned `src/tabpfn_xg` layout and distribution name `tabpfn-xg`.
- Keep the scaffold free of runtime dependencies and import side effects.
- Use setuptools as the build backend with explicit package discovery under
  `src`; research scripts and local data are not installed as package modules.
- Retain standard-library `unittest`; no third-party test runner is needed.
- Add data, app, and experiment requirements when the corresponding modules
  are migrated and their requirements can be validated. An empty extra would
  misleadingly suggest that an app or experiment is ready to install.
- Preserve the recorded research versions in the manifest; do not change the
  freeze or promise numerical parity from a scaffold installation.

Python support and validation results are recorded in the Task 2 completion
record in `TASKS.md`. No research sources, results, or credentials are copied.
