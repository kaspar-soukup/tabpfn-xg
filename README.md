# TabPFN xG

Hackathon project in preparation: explore football scoring chances with TabPFN-3.5, compare predictions, and test your football intuition.

Tasks 1 (research review and provenance) and 2 (package setup) are implemented and ready for review. Application code has not been migrated yet. See the [implementation plan](IMPLEMENTATION_PLAN.md) and [task checklist](TASKS.md).

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

Installation downloads setuptools for the isolated build. The scaffold has no runtime dependencies, and tests use standard-library `unittest`. Discovery currently finds four provenance tests, all of which skip without the research snapshot; run the source-dependent command below to actually validate it. No app or experiment extras are available yet; their dependencies will be added alongside the migrated capabilities. See the [Task 2 findings](provenance/TASK_2_SETUP.md). Older Python versions have not been checked.

The implementation will come from the original acquisition/processing notebooks and the frozen geometry/external research pipeline. The [portable provenance manifest](provenance/research_manifest.json) records 76 source hashes, exact ordered 8,000 fit shot IDs, historical/external match IDs, ordered 50 features, model settings and calibration. The [research handoff](provenance/RESEARCH_HANDOFF.md) explains migration pitfalls, artifact sizes, verification results and unresolved historical acquisition metadata.

Verify the selected research snapshot with standard-library Python, replacing the path if the snapshot has moved:

```sh
python3 scripts/verify_provenance.py --research-root /path/to/tabPFN
python3 -m compileall -q scripts tests
TABPFN_RESEARCH_ROOT=/path/to/tabPFN python3 -m unittest discover -s tests -v
```

These checks passed against the recorded local snapshot; four provenance tests and all 14 existing research backend tests passed. Without `TABPFN_RESEARCH_ROOT`, source-dependent tests skip. The verifier reads references only, performs no inference and needs no token. A clean checkout contains the provenance record, but not the research data; portable data preparation and demo assets are later tasks.

Frozen external evidence covers 908 eligible shots from 34 Bayer Leverkusen Bundesliga 2023/24 fixtures (both teams). TabPFN improves on the tested equal-data CatBoost baseline; it does not establish superiority over StatsBomb or all xG models. Source data originate from StatsBomb Open Data; the manifest pins commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. Distribution/licensing and historical public-input reconstruction remain pending. No app launch command is available yet.
