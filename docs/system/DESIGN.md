# Calisthenics system design (v0 draft)

Goal: one app that trains **stretch, strength and stamina** for a complete beginner, with progression set by the repo's lever model instead of a coach's guessed list. This is a design, not medical advice. Stop any exercise that causes pain and see a qualified professional for injuries.

Terms used once:
- **Torque**: turning force at a joint = force x perpendicular distance (Nm). Longer lever = harder.
- **Progression**: an ordered set of versions of one movement (wall pushup -> incline -> knee -> full).
- **RPE**: rate of perceived exertion, 1-10. RPE 7 = about 3 reps left in the tank.
- **End range**: the furthest a joint moves comfortably.
- **Zone 2**: easy cardio where you can still talk in full sentences.

## What the research showed (Nov 2, 2026)
Apps split into strength ladders (Hybrid Calisthenics, Calistree, Caliverse), conditioning (Madbarz, Freeletics) and mobility (Pliability, GMB). None covers all three on one model. "Adaptive" apps adjust from difficulty ratings, not physics. Leverage math only exists in standalone calculators for static holds (Calintellect, leverage.fit). Full table: Page "Calisthenics app research".

## 1. Strength: torque-scored progressions
**Fundamentals** (borrowed from Hybrid's six, mapped to muscle groups):

| Fundamental | Main joint scored | Muscle groups | Example ladder |
|---|---|---|---|
| Push | shoulder | chest, triceps, front delts | wall -> incline -> knee -> full -> decline pushup |
| Pull | shoulder | lats, biceps, rear delts | high row -> low row -> negative -> pullup |
| Squat | knee + hip | quads, glutes | box squat -> full squat -> split squat -> pistol |
| Hinge/bridge | hip | glutes, hamstrings | glute bridge -> single-leg bridge -> hip thrust |
| Core (leg raise) | hip flexors / trunk | abs, hip flexors | knee tuck -> bent leg raise -> straight leg raise |
| Twist / anti-rotation | trunk | obliques | dead bug -> side plank -> Copenhagen-style |

**Score.** For each move, `lever_load` (biomech/core.py) computes joint torque from the user's own limb lengths (biomech/measurements.py). Difficulty = torque / the user's strength reference at that joint (`relative_torque`). Today only the push pattern exists on main (moves: see data/moves.json); the other five need geometry models.

**Even steps.** The ideal next step is about +10% joint torque. Main's `recommend()` currently accepts a 10-20% band and aims at 15%, flagging jumps outside it. When the catalogue has gaps, fill them with continuous adjusters: hand height on an incline (any angle), tempo (slower lowering), pause reps, or partial range.

**Progress readout.** "You're at 82% of next level": current torque x rep quality vs next step's torque. Also show Nm per joint over time.

**Rule (already on main):** progress only when the rep target is met at RPE <= 7 with no discomfort; hold if below target; regress immediately on discomfort.

## 2. Stretch track
Joints: hips (flexors, rotators), hamstrings, shoulders, thoracic spine (upper back), ankles, wrists.

Each has 3 stages:
1. **Range**: reach a measured position (e.g. toe-touch distance in cm, wall shoulder flexion angle, knee-to-wall ankle cm). Measure with the phone camera or a tape.
2. **Hold time**: build the hold at that range from 20 s to 60 s, 2-3 sets.
3. **Loaded end range**: add light load or active holds (e.g. Jefferson curl with very light weight, active pike lift). Torque at end range can use the same lever model (limb weight x distance).

Progress = +range (cm/degrees) first, then +time, then +load. Never bounce, never push into sharp pain; mild stretch sensation at about 3-5/10 only.

**Posture and breathing basics** (part of the warm-up, 2 min):
- Slow belly breathing: lower ribs and belly expand front and sides, shoulders stay still. 4 s in, 6 s out.
- Exhale during the hard part of a stretch; the muscle relaxes more on the exhale.
- Brace for strength: breathe into the belly, then tighten as if about to be poked. This raises belly pressure and steadies the lower back.
- Desk reset: chin tuck, shoulder blades down and back, 5 slow breaths, a few times a day.

## 3. Stamina: options
| Option | How it progresses | Pros | Cons |
|---|---|---|---|
| A. Calisthenics circuits / density (same work in less time) | add rounds, or same rounds faster; fixed moves from the strength ladder at easy levels | no equipment; reuses the lever model; builds work capacity | sloppy form when tired; overlaps with strength fatigue |
| B. EMOM / AMRAP (every minute on the minute / as many rounds as possible) | EMOM: +1 rep per minute or +1 minute; AMRAP: more rounds in the same time | very measurable; short (10-15 min); fun scores | easy to go too hard as a beginner; joint stress if reps balloon |
| C. Zone-2 cardio (walk/jog, row, cycle) | +10% minutes per week, 20 -> 45 min; later pace at the same heart rate | best-evidenced aerobic base; low skill; recovers fast; doesn't tire the strength muscles much | needs time, maybe a heart-rate strap; less "calisthenics"; running adds impact |
| D. Intervals (e.g. 30 s hard / 90 s easy, bike or hill sprints) | +1 interval, then shorter rest | time-efficient; raises top-end fitness | hardest on recovery; not ideal before an aerobic base |

**My pick: C (zone-2) as the base, plus a short B (EMOM finisher) once a week after week 4.** A beginner gains the most from easy aerobic volume, it barely competes with strength recovery, and the EMOM gives a calisthenics-flavoured, scoreable test. Intervals (D) come later, after about 8 weeks.

## 4. Beginner placement test (about 20 min, measured)
Do once at start and every 6 weeks.
- **Body measurements**: height, weight, upper arm, forearm, torso, thigh, shank (tape or the lidar scan planned for the suit). Feeds the lever model.
- **Strength** (for each fundamental): start at the easiest move; do up to 10 clean reps at RPE <= 7; step up until reps < 5. Starting level = the hardest move with >= 8 clean reps. Its torque sets the strength reference for that joint.
- **Holds**: plank and side plank max time (stop at 60 s).
- **Stretch**: toe-touch (cm), knee-to-wall ankle (cm, each side), wall shoulder flexion (degrees, photo), deep-squat hold (s), wrist extension against wall (degrees).
- **Stamina**: talk-test walk/jog for 10 min (can you speak in sentences?) or resting heart rate.
- Skip any part that hurts; mark it "not tested" and start at the lowest level.

## 5. Weekly structure (complete beginner)
| Day | Session (about 30-40 min) |
|---|---|
| Mon | Strength A (push, squat, core) + 10 min stretch |
| Tue | Zone-2 25 min + breathing |
| Wed | Strength B (pull, hinge, twist) + 10 min stretch |
| Thu | Rest or easy walk + stretch 15 min |
| Fri | Strength A/B full body light + 10 min stretch |
| Sat | Zone-2 30-40 min (EMOM 10 min finisher from week 4) |
| Sun | Rest |

Each muscle group about 2x/week, 2-3 sets of 5-12 reps. Stretch most days (short). Recovery: at least 1 full rest day, about 7-9 h sleep, deload week (half the sets) every 6th week. The app pushes nothing; Ben opens it when he trains.

## 6. Logging and auto-adjust
Logged per set: move, reps (or hold seconds), RPE, discomfort yes/no + where, notes. Per stretch: range measurement, hold time, load. Per cardio: minutes, distance, average heart rate or talk-test. Body measurements with date.

Auto-adjust:
- Strength: main's `recommend()` rule (progress / hold / regress), step chosen by torque jump. Two sessions in a row missing the target at the same level -> drop one step or add an adjuster.
- Stretch: if hold target met 2 sessions -> +10 s; at 60 s -> retest range; range gain -> next position.
- Stamina: talk test passed all session -> +10% minutes next week; failed -> repeat week.
- Every 6 weeks: retest; update strength references (only via a measured test, never silently).
- Any discomfort flag -> regress and show a "see a professional if it persists" note.

## 7. App MVP scope
Screens:
1. Onboarding + placement test (guided, one step per screen).
2. Today (the planned session, tap to log each set).
3. Progressions (per fundamental: ladder with torque per step, "82% to next").
4. Stretch map (joints with current range and hold).
5. Stamina (weekly minutes, EMOM scores).
6. History & export (CSV/JSON).

Data model sketch:
```
Body(id, date, mass_kg, segment lengths...)          # biomech/measurements.py
Move(id, fundamental, joint, geometry, rep_target)   # data/moves.json, extended
StrengthRef(joint, nm, date, source=test)
Session(id, date, type=strength|stretch|stamina)
SetLog(session_id, move_id, reps|hold_s, rpe, discomfort, note)  # biomech/sessions.py
StretchLog(session_id, joint, side, range_value, unit, hold_s, load_kg)
CardioLog(session_id, mode, minutes, distance_m, avg_hr, talk_test_ok)
Decision(move_id, action, target_id, jump, reason)   # recommend() output
```
Stack (suggested, needs Ben): Python core stays the source of truth; expose via a small API (FastAPI) and a phone front end (React Native/Expo) or a PWA first. Local-first storage (SQLite).

Out of MVP: social, nutrition, video library, wearables beyond manual heart rate.

## Safety
- Warm up 5 min first. Stop on sharp, joint, or radiating pain; numbness; dizziness.
- Discomfort always regresses; the app never pushes through.
- Stretch to mild tension only; no bouncing.
- Body-model numbers are estimates from a 2D lever model, not measurements of tissue limits.
- No medical claims. Anyone with an injury or condition should check with a clinician first.

## Decisions for Ben
1. Stamina pick: zone-2 base + weekly EMOM (my pick) vs circuits vs intervals.
2. Step size: +10% target (this doc) vs main's current 10-20% band aiming 15%.
3. App form: PWA first (my pick, fastest) vs native phone app.
4. Days per week: 5 short (above) vs 3 longer.
