# Session log format

A log is a UTF-8 JSON array. Each row records **one completed set**, not a daily
total. Write rows in chronological order. Equal dates are allowed; array order
defines which set is latest on that date. There are no timestamps in v1.

```json
[
  {
    "date": "2026-10-19",
    "move_id": "wall-push-up",
    "reps": 8,
    "rpe": 7,
    "discomfort": false,
    "discomfort_notes": ""
  }
]
```

| Field | Validation |
| --- | --- |
| `date` | An actual calendar date in exact `YYYY-MM-DD` form |
| `move_id` | Nonempty string matching an ID in the loaded move catalogue |
| `reps` | Integer, zero or greater; no booleans |
| `rpe` | Finite number from 1 to 10 inclusive; no booleans or numeric strings |
| `discomfort` | JSON `true` or `false`, not text or a number |
| `discomfort_notes` | String; must contain text when discomfort is true |

All six fields are required. Unknown fields are rejected to catch spelling
errors. RPE is the user's reported effort, from lowest (1) to highest (10);
fractional reports such as 7.5 are allowed. The engine never estimates RPE
from reps or torque. Log zero reps if no rep was completed, and report actual
effort and discomfort rather than forcing the rep target.

`load_sessions(path, moves)` returns a list of validated `Session` objects.
Invalid rows raise `ValueError` with the row number. Invalid JSON, incorrect
root shape, unknown IDs, and dates that run backwards also raise `ValueError`.
File access errors raise `OSError`. An empty array is a valid stored log, but
the CLI cannot recommend a next move until a completed set has been logged.

The CLI validates the entire log, then uses the last row in the selected
pattern. It does not silently sort or repair data. Direct Python callers can
construct `Session(...)`; the same field validation applies. Move membership
and date order are checked by the loader, and `recommend` also rejects an
unknown current move.

See [example_session_log.json](../data/example_session_log.json) for a fictional
history. The software only reads logs. Keep personal logs outside the checkout;
no personal files need to be committed.
