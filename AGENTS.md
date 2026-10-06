# Agent instructions

## Project purpose and references

Build a simple, approachable football expected-goals hackathon demo using the existing research pipeline and frozen model results.

- Read `IMPLEMENTATION_PLAN.md` for the scope, research references, and evidence.
- Use `TASKS.md` as the implementation checklist and completion record.
- Use the original notebooks to understand the pipeline and the referenced research scripts and manifests to preserve its current behavior.

## Approval and questions

- Creating or updating planning documents does not authorize implementation. See `TASKS.md` for approved and completed work.
- Get the user's approval before starting an implementation task. Work on one small, testable task at a time and stop after completing it for review, unless the user explicitly changes this cadence.
- Detail the task's scope, files, dependencies, and validation before starting. Split large tasks into independently reviewable steps.
- Ask the user when requirements, expected behavior, technical choices, or scope are unclear. Do not silently choose an assumption. Inspect existing documentation and code first to avoid asking questions already answered.
- Continue independent, already approved work while waiting for clarification; do not proceed with changes that depend on the answer.

## Code quality

- Use Python 3.14; packaging must declare support for the 3.14 release series.
- Write clean, efficient, readable code with clear names and small functions that have a single purpose.
- Use the simplest design that meets the approved requirements. Avoid unnecessary abstractions, dependencies, duplication, and speculative features.
- Keep data conversion, feature construction, model inference, calibration, and evaluation separate from UI code. Reuse the same feature implementation in the app and experiments.
- Use explicit configuration and paths instead of mutable module globals or absolute research-workspace paths.
- Validate inputs at meaningful boundaries and provide actionable errors.
- Preserve the ordered 50-feature schema, exact fit sample, frozen configuration, calibration, and cached predictions. Do not retune against external evaluation outcomes.
- Leave the research workspace and original university project unchanged. Never copy or expose credentials.

## Validation responsibilities

- **Never write or run frontend tests.** The user handles all frontend testing, including browser checks, visual inspection, interaction checks, UI state tests, and end-to-end UI tests.
- Always verify that changed code compiles before handing it over. For Python, use an appropriate syntax/compilation check such as `python -m compileall`; for a frontend toolchain, use its compile/build command if one exists. Run these checks without starting browser or UI testing.
- Add and run meaningful backend tests for data processing, feature geometry, probability checks, calibration, model interfaces, and evaluation as relevant to the approved task.
- Backend tests must not exercise the UI or require live paid inference. Use fake clients for inference-interface tests where appropriate.
- Report the exact compile/build and backend test commands and their results. If a check cannot run, state the reason; do not report it as passed.
- For UI changes, provide concise manual validation steps for the user. Mark frontend acceptance as pending user validation until the user confirms it.

## Documentation and completion

- Update `README.md` alongside every implemented capability with setup or usage instructions, validation commands, and relevant limitations.
- Keep `TASKS.md` current with task status, changed files, checks and results, README updates, outstanding questions, and review status.
- Separate completed implementation and compilation from pending user frontend validation. Do not mark frontend acceptance as verified on the user's behalf.
- Document model comparisons accurately and include data provenance and attribution. Claims must reflect the frozen external results and their uncertainty.
- End each task with a concise explanation of what changed, how it was checked, and what the user should review.
- Commit completed task changes after the required validation and documentation updates, unless the user asks otherwise. Do not include unrelated changes.
