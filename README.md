# Biomechanics

A local calisthenics progression framework for a complete beginner. V1 covers
four push movements: wall, incline, knee, and full push-ups. It estimates one
planar shoulder lever per movement, ranks the moves for your dimensions, and
uses a completed set to suggest **hold**, **progress**, or **regress** with a
reason. Muscle groups are tags; they do not have separate levers.

This is an inspectable model, not a measured strength assessment or a validated
training prescription. Read the [model and limits](docs/model.md) before using
the numbers. The CLI reads local JSON and prints JSON. It does not change logs,
collect data, or use the network. Python 3.10+ and its standard library are all
you need. There are no installs.

## Quick start

From the repository root, run the supplied example:

```sh
python3 -m biomech --body data/example_body.json --moves data/moves.json --log data/example_session_log.json --strength-reference 150
```

The example uses a fictional 70 kg body and a **bilateral** shoulder strength
reference of 150 Nm. That reference is an example normalization value, not a
strength estimate for you. The output ranks the moves and suggests knee push-ups
after the last logged incline set: 8 reps at RPE 7, without discomfort. Its
estimated relative torque is 16.5% higher.

To use your own inputs:

1. Make a private copy of [example_body.json](data/example_body.json). Enter your
   mass in kg and segment lengths in metres using the
   [measurement interface](docs/measurements.md).
2. Start with the easiest ranked move you can perform without discomfort. Record
   one completed set in a private JSON log using the [session format](docs/sessions.md).
3. Run the same CLI with your file paths and an explicit positive strength
   reference. See the model for its units and interpretation. RPE runs from 1
   (lowest effort) to 10 (highest effort); the progress threshold is 7.
4. Read `decision.reason`. A flagged jump needs review because the catalogue
   has no suitable 10–20% step. A discomfort result means stop the current move;
   an easier option is only for after discomfort resolves. At the bottom,
   `move_id` is `null`.

Keep personal measurement and session files outside this checkout. V1 has no
calendar, set-volume plan, or automatic log writer. The CLI uses the latest set
in the selected pattern; an empty log produces a clear error. See
[docs/api.md](docs/api.md) for direct Python use.

## Verify

This one command runs the full acceptance suite, the CLI example, and the
eight-session beginner simulation:

```sh
python3 scripts/verify.py
```

It exits with a nonzero status on failure and writes
`artifacts/verification.json`. The artifact includes test counts, full test
output, the simulated session/decision trace, and example CLI output. It is
generated locally and ignored by Git. Rerun the command to reproduce it.

## Files

| Path | Purpose |
| --- | --- |
| `biomech/` | Lever math, ranking, decisions, validated loaders, read-only CLI |
| `data/` | Four move definitions and fictional body/session examples |
| `docs/model.md` | Equations, hand calculation, progression policy, limits |
| `docs/measurements.md` | Manual/JSON dimensions and unimplemented PLY adapter |
| `docs/sessions.md` | Session schema and validation rules |
| `docs/api.md` | Python interface and error contract |
| `tests/` | Hand calculations, validation checks, and CLI acceptance scenarios |
| `STATUS.md` | Completed scope, evidence, and next work |
