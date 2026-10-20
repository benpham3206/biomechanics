# Python interface

Run from the repository root or put the repository on Python's module path.
No package installation is needed. The modules use only the standard library.

```python
from biomech.core import lever_load, load_moves, rank_moves, recommend
from biomech.measurements import load_body
from biomech.sessions import load_sessions

body = load_body("data/example_body.json")
moves = load_moves("data/moves.json")
sessions = load_sessions("data/example_session_log.json", moves)

ranked = rank_moves(moves, body, strength_reference_nm=150, pattern="push")
load = lever_load(ranked[0].move, body)
decision = recommend(sessions[-1], moves, body, strength_reference_nm=150)
assert decision.action == "progress"
assert decision.move_id == "knee-push-up"
```

| Interface | Output |
| --- | --- |
| `load_moves(path)` | Nonempty list of validated `Move` records with unique IDs |
| `lever_load(move, body)` | `LeverLoad(hand_force_n, moment_arm_m, torque_nm)` |
| `rank_moves(moves, body, strength_reference_nm, pattern)` | Ascending list of `RankedMove(move, load, relative_torque)` |
| `recommend(session, moves, body, strength_reference_nm)` | `Decision(action, move_id, reason, jump_fraction, flagged_jump)` |

Loaders accept strings or `pathlib.Path`. Functions do not mutate the inputs.
Python callers supply validated `BodyDimensions`, `Move`/`Geometry`, and
`Session` records. Use the dataclass constructors or JSON loaders. Both check
fields; geometry that produces a nonpositive hand projection is rejected when
calculating its load. Keep catalogue lists unchanged while using them.

Invalid numeric values, malformed records, duplicate move IDs, unsupported
geometry, an unknown pattern, and an unknown current move raise `ValueError`.
File access errors raise `OSError`. `load_ply` raises `NotImplementedError`.
The CLI reports input errors on stderr and exits with status 2. Successful
output is a JSON object with `pattern`, `ranking`, `latest_session`, and
`decision`. It exits with status 0 and writes no files.

## Move catalogue schema

Each object in [moves.json](../data/moves.json) requires `id`, `name`, `pattern`,
`muscle_groups`, `geometry`, and `rep_target`. Names, IDs, and patterns are
nonempty strings; muscle groups are a nonempty array of nonempty strings.
The rep target is a positive integer. Unknown or missing fields are errors.

Geometry requires exactly these fields:

- `support_segments`: nonempty array of unique field names selected from
  `torso_m`, `thigh_m`, `shank_m`.
- `mass_fraction`, `com_fraction`: finite numbers greater than 0 and at most 1.
- `body_angle_deg`: finite number from 0 inclusive to 90 exclusive.
- `upper_arm_angle_deg`, `elbow_angle_deg`: finite numbers from -180 to 180.

Booleans are rejected as numbers. The calculated headward shoulder-to-hand
projection must be positive, and computed force, torque, and relative torque
must be finite and positive. The model supports this particular geometry only;
adding a pull or squat name to the file does not validate that movement's
mechanics. A new pattern needs its own justified movement model and checks.
