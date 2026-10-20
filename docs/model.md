# V1 movement model

## Scope and conventions

V1 has **one planar (2D) lever model per movement**. The output metric is the
external shoulder moment, summed across both shoulders under equal load
sharing. It is not a separate lever for each muscle and does not estimate
elbow torque. `muscle_groups` only tags the movement.

The equations below define this model; they are not fitted to human force-plate
data. Force is in newtons (N), lengths in metres (m), torque in newton-metres
(Nm), and stored angles in degrees. Calculations convert angles to radians.

## Geometry and free-body assumptions

Treat the supported body as a rigid link with a pivot `O` at the feet (wall,
incline, full) or knees (knee variant). Let `b` point along the body from the
pivot toward the shoulders. Let `n` be the perpendicular direction toward the
support reaction. The body is inclined by `theta` above horizontal.

| Symbol | Source | Meaning |
| --- | --- | --- |
| `m` | `body.mass_kg` | Whole body mass |
| `g` | 9.81 | Gravitational acceleration, m/s² |
| `f` | `geometry.mass_fraction` | Assumed fraction of mass borne by this rigid link |
| `S` | Sum of `support_segments` | Pivot-to-shoulder span along `b` |
| `k` | `geometry.com_fraction` | Centre-of-mass station as a fraction of `S` |
| `c = k S` | Derived | Pivot-to-centre-of-mass distance along `b` |
| `u`, `v` | Upper-arm, forearm lengths | Shoulder-to-elbow and elbow-to-wrist lengths |
| `alpha` | `upper_arm_angle_deg` | Upper arm orientation relative to `b` |
| `beta` | `elbow_angle_deg` | Signed forearm turn relative to the upper arm |
| `theta` | `body_angle_deg` | Body inclination above horizontal |

`beta` is a signed segment turn, **not** the anatomical internal elbow angle.
The forearm orientation relative to the body is `alpha + beta`.
Each move describes one representative bent-arm pose, not an entire repetition.

There is no applied couple at the pivot. Both hands together exert a modeled
force `F` along `n`. Any body-parallel gravitational component is carried by the
pivot reaction. Thus the hand reaction has no component along `b` in this
model. This is an explicit closure assumption, not a universal contact law.

The shoulder-to-hand vector is

```text
r = (u cos(alpha) + v cos(alpha + beta)) b
  + (u sin(alpha) + v sin(alpha + beta)) n

d = u cos(alpha) + v cos(alpha + beta)
H = S + d
```

V1 requires `d > 0`: the hand projection is headward of the shoulder. `H` is
the perpendicular distance from the pivot to the line of action of `F`.
It is derived from the body and arm lengths, rather than stored as a
difficulty score. Other hand placements need a revised geometry contract.

## Force and joint torque

For a planar joint, the magnitude of external torque is

```text
tau = |r x F| = |F| * d_perpendicular
```

The effective weight is `W = f m g`, vertically downward at `c b`. Its
perpendicular moment arm about `O` is the horizontal distance `c cos(theta)`.
Balancing moments about the pivot gives

```text
F H = W c cos(theta)
F = f m g k S cos(theta) / (S + d)
tau_shoulders = F d
```

The body-normal component of hand loading decreases with inclination through
`cos(theta)`. The CLI field `hand_force_n` is this **total transverse load
across both hands**. Under the equal-sharing assumption, each hand bears
`F / 2`, and each shoulder's external moment is `F d / 2`. The returned
`torque_nm` is the sum `F d`, and the strength reference must use that same
bilateral convention.

The inclination effect must not be confused with total measured hand force.
For example, a model with purely vertical hand reactions and both COM and hand
stations on the same inclined straight line has the same cosine in numerator
and denominator, so it cancels. Our body-normal reaction assumption is what
produces the cosine reduction. Real wall/floor contacts, friction, hand
placement, and segment motion can produce different forces.

## Worked hand calculation

Use `data/example_body.json`:

```text
m = 70 kg
torso = 0.55 m, thigh = 0.45 m, shank = 0.45 m
u = 0.30 m, v = 0.25 m
alpha = -60 degrees, beta = +60 degrees
d = 0.30 cos(-60) + 0.25 cos(0) = 0.15 + 0.25 = 0.40 m
```

For a full push-up, `f = 1`, `k = 0.60`, and `theta = 0`:

```text
S = 0.55 + 0.45 + 0.45 = 1.45 m
c = 0.60 * 1.45 = 0.87 m
H = 1.45 + 0.40 = 1.85 m
W = 70 * 9.81 = 686.70 N
weight moment about feet = 686.70 * 0.87 = 597.429 Nm
F = 597.429 / 1.85 = 322.9346 N (both hands)
tau_shoulders = 322.9346 * 0.40 = 129.1738 Nm
tau_one_shoulder = 64.5869 Nm
```

With the same geometry, a 55-degree incline gives
`F = 322.9346 * cos(55) = 185.2277 N` and
`tau = 185.2277 * 0.40 = 74.0911 Nm`.

For the knee variant, remove the shank from the span and assume `f = 0.80`,
`k = 0.55`, `theta = 0`:

```text
S = 0.55 + 0.45 = 1.00 m
c = 0.55 * 1.00 = 0.55 m
W = 0.80 * 70 * 9.81 = 549.36 N
H = 1.00 + 0.40 = 1.40 m
F = 549.36 * 0.55 / 1.40 = 215.82 N
tau = 215.82 * 0.40 = 86.328 Nm
```

The knee mass/COM fractions and default angles are **model estimates**, not
measured population constants. The shorter support span and effective mass
are what distinguish the knee move here. The catalogue is not an empirical
strength scale.

## Difficulty and ranking

Let `T_ref > 0` be the user's external bilateral shoulder strength reference
in Nm, in the same pose convention:

```text
relative_torque = tau_shoulders / T_ref
```

This dimensionless ratio is the difficulty metric. It is not RPE or a
prediction of maximum reps. V1 accepts `T_ref` as an explicit input; it does
not infer strength from body mass, logs, or point clouds. The example value
150 Nm is illustrative. There is no strength calibration protocol in v1.

Rank only within a movement pattern, using ascending relative torque, with
move ID as a deterministic tie-break. A common positive reference changes
the absolute ratios but cancels when comparing percentage increases within
that pattern. A ratio above 1 does not trigger an extra rule in v1.

For the example body and `T_ref = 150 Nm`:

| Move | Inclination | Total transverse hand force | Bilateral torque | Relative torque | Jump from previous |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wall push-up | 75° | 83.5816 N | 33.4326 Nm | 0.2229 | — |
| Incline push-up | 55° | 185.2277 N | 74.0911 Nm | 0.4939 | 121.6%, flagged |
| Knee push-up | 0° | 215.8200 N | 86.3280 Nm | 0.5755 | 16.5% |
| Full push-up | 0° | 322.9346 N | 129.1738 Nm | 0.8612 | 49.6%, flagged |

This order is calculated, not hard-coded. Different dimensions or geometry
can change it. All four moves have a target of 8 completed reps.

## Progression policy

Use the latest completed set in the current pattern. Apply rules in this order:

1. **Regress on any discomfort**, regardless of reps or RPE. Stop the current
   move. Suggest the highest-torque strictly easier move for after discomfort
   resolves. If none exists, return `regress` with `move_id = null` and a stop
   reason. Never recommend continuing through discomfort.
2. **Hold** if reps are below the move's target, or if RPE is above 7.
3. Otherwise, consider all strictly harder moves in that pattern. Define
   `jump = relative_next / relative_current - 1`. Prefer a jump in the inclusive
   10–20% band, closest to 15%. If tied, pick the lower-torque candidate.
4. If no move is in that band, **pick the closest available harder move to
   15% and flag it**. This covers a jump larger than 20%, and also a catalogue
   with only jumps smaller than 10%. The reason states the percentage and
   that it is outside the band. It is a suggestion for review, not an
   automatic instruction to attempt the larger jump.
5. At the top, **hold** with an explicit ceiling reason. Equal-torque moves
   are neither progression nor regression options.

All results contain an action, target move ID, and reason string. Only
progression results contain `jump_fraction`; `flagged_jump` is false otherwise.
The 10–20% band is the requested policy heuristic, not an injury-risk estimate
or a demonstrated optimum for adaptation. The engine does not apply the
recommendation, change the strength reference, or alter session history.

## Assumptions and limits

- Static 2D balance at one representative pose. No acceleration, fatigue
  dynamics, tendon moment arms, joint compression, or force distribution
  between individual muscles.
- Fixed estimated COM and supported-mass fractions. No mass distribution
  calculation from the measured segments. Equal left/right load sharing.
- The body-normal hand reaction and freely reacting pivot are abstractions.
  The model does not enforce floor/wall contact closure, friction limits,
  contact heights, wrist orientation, or anatomical joint limits. A horizontal
  link is a reference geometry, not a complete photograph of a floor push-up.
- No load-path change through a repetition. A single shoulder metric cannot
  capture elbow, wrist, trunk, balance, range-of-motion, or technique limits.
- Angles are inputs, not measurements. Different wall distances, incline
  heights, and hand positions can change real difficulty. A PLY cloud alone
  cannot establish these forces or the user's strength.
- A single logged set can trigger progression; no multi-session confirmation,
  recovery schedule, volume prescription, or medical assessment is implemented.
- Verification proves arithmetic and software policy against these assumptions.
  No human training outcomes, force-plate measurements, or LiDAR calibration
  have been validated.
