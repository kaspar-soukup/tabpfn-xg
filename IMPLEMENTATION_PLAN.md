# TabPFN xG hackathon: implementation plan and source references

Created: 2026-10-06. Target repository: `/Users/kasparsoukup/Documents/_Documents/Projects/tabpfn-xg`.

## Purpose and current state

Create a focused hackathon submission that lets visitors explore football scoring chances with TabPFN-3.5, compare models, and test their own football intuition. This new repository currently contains the plan and setup notes; the application and pipeline have not been migrated yet.

The research workspace remains at `/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN`, branch `xg-tabpfn`. Its HEAD at handoff is `11cb8723984c85b57828935cad4fd95e2525ba2d`. Some referenced implementation files are uncommitted and experiment outputs/data are Git-ignored: exporting HEAD alone will not capture all required work. Read the actual working-tree files and preserve their hashes when migrating.

The original university project remains at `/Users/kasparsoukup/Documents/__Fulbright/_Columbia/Studies/1st Semester/Data Analytics/Group Project/Expected-Goals`. Work from the research workspace; leave the original project untouched.

## Project story and evidence

Suggested pitch: “Explore football chances with TabPFN-3.5: predict goals from shot geometry and visible defenders, compare against conventional models, and test your own football intuition.”

The frozen geometry models use 50 predictors: 37 original features plus nine defender/pressure features and four goal-coverage features. TabPFN-3.5 and CatBoost use the same 8,000-shot fit sample, seed 123, and calibration learned from separate historical calibration matches. Model/calibration choices preceded the external test; no external outcomes entered fitting or calibration.

External test: 908 eligible shots, 102 goals, 34 Bundesliga 2023/24 matches, all Bayer Leverkusen league fixtures with both teams' shots. None overlap the local dataset. Eligible shots are Open Play or Free Kick with an observed opposition goalkeeper; eight penalties were excluded.

| Model | Log loss (lower is better) | Brier (lower is better) | AUC (higher is better) |
| --- | ---: | ---: | ---: |
| StatsBomb | 0.289131 | 0.082558 | 0.787428 |
| TabPFN-3.5 | 0.293712 | 0.084286 | 0.781808 |
| CatBoost | 0.301381 | 0.087070 | 0.772405 |

TabPFN has 2.54% lower log loss and 3.20% lower Brier than our equal-data CatBoost baseline. The paired match-bootstrap 95% intervals exclude zero for both differences. StatsBomb scores better on point estimates, but both difference intervals include zero. The earlier exploratory edge over StatsBomb did not repeat. Claim an improvement over our tested CatBoost baseline, not over StatsBomb or every conventional xG model. The public external sample covers one club's season, and StatsBomb's model version/training data are unknown.

## MVP experience

1. Show a real shot on a pitch with the shooter, goalkeeper and visible defenders. Hide the outcome initially.
2. Let the visitor estimate its scoring probability.
3. Reveal TabPFN, CatBoost and the supplied StatsBomb probabilities.
4. Reveal the observed outcome and explain the shot geometry (angle, distance, nearby defenders and approximate blocked goal coverage).
5. Offer another shot and a page showing aggregate evaluation results. One observed outcome does not establish whether a probability was correct.

Use a cached demo with real, previously computed predictions so visitors can run it without a token. Label cached predictions clearly. Add live TabPFN inference when a server-side token is configured.

Optional after the core demo works: a “change the chance” interaction that moves a defender or keeper and recomputes shared features and model predictions. StatsBomb's supplied xG is valid only for the original shot; do not display it as a fresh prediction for edited geometry. Counterfactual edits illustrate model behavior, not causal effects. Keep annotations consistent with edits or constrain which edits are allowed.

## Proposed repository structure

```text
src/tabpfn_xg/
    data.py          # Public event download, conversion, eligibility checks
    features.py      # One shared feature implementation and ordered schema
    models.py        # Frozen TabPFN and CatBoost configuration/interfaces
    calibration.py   # Existing calibration parameters and application
    evaluation.py    # Metrics, paired match bootstrap and reports
scripts/
    prepare_data.py
    run_experiment.py
app.py
tests/
reports/
README.md
pyproject.toml
.env.example
```

Extract the necessary pipeline, not every notebook. Keep historical exploration and abandoned experiments in the research repository. An optional explanatory notebook must not be required to run the application.

## Implementation sequence

### Day one: correctness and core interaction

- [ ] Snapshot the selected research files and record hashes, source match IDs, exact fit IDs, feature order, configuration and calibration. Keep existing experiment outputs unchanged.
- [ ] Extract event conversion and geometry into the shared package. The app and experiments must call the same feature builder.
- [ ] Move model construction, probability/class checks, calibration and evaluation into small modules with explicit configuration and paths rather than mutable module globals.
- [ ] Preserve the 50-feature geometry variant and the original fit sample/calibration. Do not tune against the external evaluation outcomes during cleanup.
- [ ] Verify migrated features and cached predictions match the research version; port the meaningful existing tests.
- [ ] Define a reproducible way to obtain the historical fit context and external demo data. Preserve provenance and StatsBomb attribution. Do not rely on absolute paths to private local pickles for public setup.
- [ ] Build the real-shot guessing interaction, probability comparison and outcome reveal. Cached mode comes first.

### Day two: submission polish

- [ ] Add a results page with the external-test table, bootstrap intervals, calibration plot and concise limitations.
- [ ] Add optional live TabPFN inference, keeping credentials server-side. Cached mode must remain available when live inference is unavailable.
- [ ] Write a focused README: purpose, screenshot, setup, one launch command, optional token configuration, data preparation, experiment reproduction and findings.
- [ ] Replace the inherited placeholder packaging/dependencies with those actually needed; choose and verify a supported Python version. The research environment currently runs Python 3.14, while the old pyproject specifies Python 3.10 only.
- [ ] Test installation and cached demo from a clean checkout, with no access to the research workspace or its `.env`.
- [ ] Check that no credentials, environments, large raw pickles or unrelated project files are tracked. Add appropriate code licensing and data-source attribution.
- [ ] Record a short demo video. Add live geometry editing only if the core experience, setup and reporting are already solid.

## Local code references

These are absolute local links into the research workspace. They are handoff references, not portable runtime dependencies. Replace them with links to migrated files in the public README.

| Source | Use in the new project |
| --- | --- |
| [xg_external_data.py](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/scripts/xg_external_data.py) | Convert native StatsBomb JSON into the original feature schema; category validation, eligibility and labels. |
| [xg_features.py](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/scripts/xg_features.py) | The 13 defender/goal-coverage features and fixed geometry settings. |
| [xg_tabpfn_pilot.py](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/scripts/xg_tabpfn_pilot.py) | Ordered 37-feature schema, split/sampling logic, model configuration, positive-class probabilities, calibration, metrics and paired match bootstrap. |
| [xg_geometry_experiment.py](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/scripts/xg_geometry_experiment.py) | Feature-bundle experiment and calibration selection. Refactor its shared logic rather than copying mutable global output paths. |
| [xg_external_experiment.py](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/scripts/xg_external_experiment.py) | Pinned public source commit, predefined match selection, overlap checks, frozen model transfer test and resumable inference. |
| [Feature documentation](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/docs/xg_features.md) | Feature meanings, coordinate units, visibility limitations and approximate blocker geometry. |
| [Pilot plan](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/XG_TABPFN_TEST_PLAN.md) | Original evaluation protocol and leakage safeguards. |
| [Research README](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/README.md) | Existing setup and experiment commands. |
| [Current app](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/app.py) | UI reference only. It loads an older CatBoost model, uses stale paths, and calculates/scales features differently from our current experiments. Replace prediction logic with the shared pipeline. |
| [Original processing notebook](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/notebooks/Processing.ipynb) | Historical feature derivation; the new converter already reproduces all 45,185 eligible original shots (max feature difference 1.42e-14, identical labels). |
| [Original data notebook](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/notebooks/Getting_data.ipynb) | Historical acquisition context; original data were selected from 2015/16 competitions. |

## Tests to migrate

- [Pilot tests](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/tests/test_xg_pilot.py): positive class mapping, calibration, nested sampling and paired cluster bootstrap.
- [Geometry tests](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/tests/test_xg_features.py): teammate/keeper exclusion, blockers, missing observations, degenerate geometry and symmetry.
- [External conversion tests](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/tests/test_xg_external_data.py): schema, outcome/reference independence, exclusions and unknown categories.

All 14 tests passed before this handoff. Add migration checks where they establish feature/prediction parity; avoid tests that simply repeat the implementation.

## Reports, frozen state and data references

| Reference | Purpose |
| --- | --- |
| [Pilot report](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/reports/xg_tabpfn_pilot.md) | Initial historical match-disjoint comparison. |
| [Geometry report](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/reports/xg_geometry_experiment.md) | Exploratory feature improvement; reused evaluation matches. |
| [External report](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/reports/xg_external_bundesliga_2023_24.md) | Main submission evidence and interpretation. |
| [Pilot manifest](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_pilot/manifest.json) | Historical input hashes, features, versions and role counts. |
| [Pilot splits](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_pilot/splits.csv) | Original shot IDs and match-disjoint roles. |
| [Geometry manifest](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_geometry/manifest.json) | Fixed geometry settings and source provenance. |
| [Geometry selection](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_geometry/selection.json) | Frozen geometry CatBoost/TabPFN calibration parameters and variants. |
| [Geometry features](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_geometry/features.csv) | Existing 13-feature table, aligned with historical processed rows. |
| [External manifest](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_external_bundesliga_2023_24/manifest.json) | Pinned source commit, all selected match IDs, exact 8,000 fit shot IDs and frozen configuration. |
| [External predictions](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_external_bundesliga_2023_24/evaluation_predictions.csv) | Cached real-shot predictions and outcomes; join by shot ID to event geometry for the demo. |
| [External paired differences](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_external_bundesliga_2023_24/paired_differences.json) | Match-bootstrap confidence intervals. |
| [External reliability plot](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_external_bundesliga_2023_24/reliability.png) | Calibration visualization. |
| [External execution audit](/Users/kasparsoukup/Documents/_Documents/Projects/tabPFN/results/xg_external_bundesliga_2023_24/execution_audit.json) | Code hashes, parity check, test count and inference timings. |

Historical local data: `tabPFN/data/processed/football_processed.pickle`, `tabPFN/data/processed/football_model_processed.pickle` and `tabPFN/data/raw/football_copy.pkl`. Downloaded external JSON and metadata: `tabPFN/data/external/bundesliga_2023_24/`. These data and the results directories are ignored by Git in the research workspace.

## Public references

- [StatsBomb Open Data](https://github.com/hudl/open-data): source events, match metadata, attribution and data-use instructions. Use the commit recorded in the external manifest when reproducing that test.
- [StatsBomb xG methodology discussion](https://www.hudl.com/blog/upgrading-expected-goals): background on incorporating goalkeeper/defender positioning; not evidence of the version behind our supplied xG values.
- [Prior Labs TabPFN-3.5 technical report](https://priorlabs.ai/technical-reports/tabpfn-3-5): model background.
- [Prior Labs API key page](https://platform.priorlabs.ai/account/api-keys): optional hosted-inference setup. Use `TABPFN_TOKEN`; never copy the research `.env` into version control.

## Definition of ready to submit

The cached app runs from a clean checkout; live inference uses the same feature schema; experiments have documented reproduction commands; model comparisons and uncertainty are honest; the repository contains a clear README, source attribution, meaningful tests, a screenshot and a short demo video. Cleanup must preserve the measured model behavior.
