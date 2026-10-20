# V1 status

## Implemented

- One static 2D movement model with total transverse hand force and bilateral
  external shoulder torque. Equations and hand calculations are in `docs/model.md`.
- Ten data-driven push steps, muscle tags, geometry, and 8-rep targets.
- Relative-torque ranking using an explicit positive strength reference.
- Progress/hold/regress decisions with reasons, discomfort priority, a 10–20%
  target band, flagged fallback jumps, and explicit bottom/top behavior.
- Strict JSON body, move, and session loaders; manual dimension construction.
- Documented lidar-viewer PLY interface that raises `NotImplementedError`.
- Read-only JSON CLI with clear input errors.
- Acceptance suite written before implementation: hand calculations, body/pose
  sensitivity, ranking, progression cases, validation, and a 14-session
  beginner run through the CLI from outside the checkout. The run traverses
  every push step, holds for missed reps/high effort, and recovers from discomfort.
- CLI checks require every consecutive push jump to be 10–20% for the example
  body at two strength references, with reversed file order and misleading names.
  Incline poses reconstruct their nominal support heights for that body.
- One verification entry point with a repeatable local JSON evidence artifact.

## Acceptance

Verified on 2026-10-19 with Python 3.14.7: all 16 checks passed, including the
CLI example and 14-session beginner simulation. The ten-step pattern has nine
consecutive torque jumps from 12.4% to 18.6%. Counter/table inclines fill the
wall-to-knee gap; foot-supported 45 cm bench and 25 cm step inclines bridge
knee to full. No eccentric movement is represented as a static progression.

The original move IDs remain valid. `incline-push-up` now uses an explicit
75 cm table pose; re-evaluating old incline logs uses that new geometry. Wall,
knee, and full geometry are unchanged. Nominal heights are calculated for the
example body, not calibrated for all users. See `docs/model.md` for the poses,
height equation, complete step table, and limits.

The new acceptance checks failed against the old catalogue before the data
change. Run the README verification command for current evidence in
`artifacts/verification.json`, including the full CLI ranking, unrounded gap
checks, and beginner trace. An isolated mutation of the high rail angle to 65°
kept the rank order but caused the CLI gap assertion to fail above 20%; its
output is in `artifacts/push-step-mutation.json`. Both artifacts stay local and
are ignored by Git.
This task uses local commits on `push-pattern-steps`; no remote publication
is included.

## Next

- Calibrate representative poses, COM estimates, and contact forces against
  measurements before making claims about human difficulty or outcomes.
- Define a strength-reference calibration method in the same bilateral convention.
- Inspect an actual lidar-viewer PLY export and establish scale, landmark
  extraction, uncertainty, and the separate mass input before implementing it.
- Add other movement patterns only with justified models and acceptance cases.

These are future work. No hardware, PLY parsing, clinical validation, or human
training trial is included in v1.
