# Task 5 probability and calibration findings

Reviewed 2026-10-06. User authorized Task 5 implementation, Task 4 provenance
and task-checklist review, validation and a commit. Scope is probability checks
and application of already frozen calibration; no refitting or inference.

## References and preserved behavior

Read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `TASKS.md`, `README.md`,
`RESEARCH_HANDOFF.md`, `TASK_4_FEATURES.md` and relevant portable manifest
sections. Reviewed the pilot's probability/calibration functions and tests, and
the external experiment's cache and calibration application path. Task 4's
50-feature implementation and geometry behavior are unchanged.

The pilot maps positive probabilities by finding class 1 in `classes_`, checks
the two-column matrix shape and unit row sums, and checks the positive vector
for finite values in `[0,1]`. Migration also validates the other class column,
requires exactly two classes, rejects complex probabilities and reports which
boundary failed. Normal frozen inputs and the source's row-sum tolerance
(`rtol=1e-5`, `atol=1e-8`) retain their behavior. Empty vectors/batches are valid;
scalar and two-dimensional probability vectors are rejected.

Use geometry selection parameters, not the earlier 37-feature pilot selection:

| Model | a | b | clip |
| --- | ---: | ---: | ---: |
| CatBoost | 1.0123564537857361 | 0.08384092826439743 | 1e-7 |
| TabPFN | 1.023112240680613 | 0.070507598294854 | 1e-7 |

`Calibration` is immutable and explicit. Parameters must be finite, `a > 0`
(matching the source optimizer constraint), and `0 < clip < 0.5`.
`apply_calibration` validates input before clipping, then applies
`sigmoid(a * logit(clipped p) + b)`. NumPy preserves the source logit arithmetic;
the sigmoid branches on sign to avoid exponential overflow. Large finite
coefficients may saturate to 0/1; this is allowed. No SciPy dependency is needed.
The two frozen constants are checked against the portable manifest and the
original geometry selection file. No mutable output paths or research runtime
dependencies are introduced.

The research calibration-recovery test fits synthetic outcomes. Fitting is
outside Task 5's frozen-application scope, so migration tests its known
`[1.5,-.4]` distortion using analytic probability anchors instead. Additional
tests cover identity, endpoints, clipping, monotonicity, invalid configuration,
input immutability, empty batches and sigmoid stability. Positive-class testing
uses a fake model and makes no service requests.

## Validation and handoff

An optional `TABPFN_RESEARCH_ROOT` test reads the two raw NPZ caches with
`allow_pickle=False`, verifies exact unique shot-ID alignment to the 908-row
external predictions CSV, and applies the recorded frozen parameters. All
values reproduce the CSV at `atol=2e-14`, `rtol=0`. Measured maximum absolute
differences are CatBoost `1.1102230246251565e-16` and TabPFN
`1.6653345369377348e-16`, consistent with floating-point arithmetic and CSV
serialization. Supplied StatsBomb values also pass probability validation.

Exact compile/backend/dependency/diff commands are recorded in `TASKS.md` and
README. Compilation passed; portable suite 34 passed/ten skipped; source-enabled
suite all 44 passed, including all 76 source hashes. No frontend checks, model
fitting, calibration fitting, inference, downloads or research modifications.

Task 6 can use `positive_probability` with a model interface and then apply the
appropriate frozen constant. Calibrate raw predictions once only: the external
evaluation CSV already holds calibrated CatBoost/TabPFN probabilities. Never
apply these constants to provider xG. Model construction remains unimplemented
and requires its own authorization. No Task 5 requirement remains unresolved.
