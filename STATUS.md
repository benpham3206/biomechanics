# V1 status

## Implemented

- One static 2D movement model with total transverse hand force and bilateral
  external shoulder torque. Equations and hand calculations are in `docs/model.md`.
- Four data-driven push moves, muscle tags, geometry, and 8-rep targets.
- Relative-torque ranking using an explicit positive strength reference.
- Progress/hold/regress decisions with reasons, discomfort priority, a 10–20%
  target band, flagged fallback jumps, and explicit bottom/top behavior.
- Strict JSON body, move, and session loaders; manual dimension construction.
- Documented lidar-viewer PLY interface that raises `NotImplementedError`.
- Read-only JSON CLI with clear input errors.
- Acceptance suite written before implementation: hand calculations, body/pose
  sensitivity, ranking, progression cases, validation, and an eight-session
  beginner run through the CLI from outside the checkout.
- One verification entry point with a repeatable local JSON evidence artifact.

## Acceptance

Verified on 2026-10-19 with Python 3.14.7: all 15 checks passed, including the
CLI example and eight-session beginner simulation. In an isolated temporary
copy, removing the inclination cosine caused both the wall and incline hand
calculations to fail as expected. No production source was changed by that check.

Run the README verification command for current evidence in
`artifacts/verification.json`. The extra formula check is recorded in
`artifacts/mutation-check.txt`. Both artifacts stay local and are ignored by Git.
This task uses local commits on `v1-lever-model`; no remote publication is included.

## Next

- Calibrate representative poses, COM estimates, and contact forces against
  measurements before making claims about human difficulty or outcomes.
- Add intermediate support heights/poses to reduce the flagged catalogue gaps.
- Define a strength-reference calibration method in the same bilateral convention.
- Inspect an actual lidar-viewer PLY export and establish scale, landmark
  extraction, uncertainty, and the separate mass input before implementing it.
- Add other movement patterns only with justified models and acceptance cases.

These are future work. No hardware, PLY parsing, clinical validation, or human
training trial is included in v1.
