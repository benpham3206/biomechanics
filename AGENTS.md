# Biomechanics engineering guide

This is a Python standard-library calisthenics lever model. See `README.md`
for use, `docs/model.md` for the physical assumptions, and `STATUS.md` for scope.

## Map

- `biomech/core.py`: movement geometry, torque, ranking, and progression.
- `biomech/measurements.py`: manual/JSON dimensions and the unimplemented PLY adapter.
- `biomech/sessions.py`: completed-set schema and chronological log validation.
- `biomech/__main__.py`: read-only JSON CLI.
- `biomech/validation.py`: shared boundary checks.
- `biomech/suit.py`: mech-suit hip lever, gas-strut assist (`V0_STRUT`), and safety check (see `docs/mech-suit/SPEC.md`, `BUILD.md`).
- `scripts/assist_curve.py`: prints the suit's assist curve and load cases.
- `data/`: fictional examples and the four-move push catalogue.
- `tests/test_framework.py`: arithmetic checks and CLI acceptance scenarios.
- `scripts/verify.py`: the sole verification entry point and artifact writer.

## Hazards

Keep units in SI and torque bilateral. The hand force is body-normal, not a
force-plate measurement. Muscle groups are tags, never separate levers. Do not
present estimated geometry, mass fractions, or progression rules as measured
human outcomes. Discomfort must override all progress conditions. Keep the PLY
adapter unimplemented until export units and landmarks can be established.

Use Python 3.10+ and its standard library only. Write failure cases before
changing logic. Prefer CLI acceptance scenarios and retain repeatable evidence.
Keep real measurements, logs, credentials, and generated artifacts out of Git.

## Verify

Run `python3 scripts/verify.py` before committing. It runs all checks and writes
`artifacts/verification.json`; nonzero exit means failure.

Work on a feature branch and open a PR. Commits, branch pushes and PRs are
fine. Merging or pushing to `main` needs Ben's explicit yes. Keep the
canonical Git safety guard enabled.
