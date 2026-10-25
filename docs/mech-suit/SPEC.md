# Mech suit v0 spec: hip and low-back lift amplifier

**Status:** draft for Ben's concept pick. Nothing is bought or built yet.
**Goal (Ben, Oct 24):** "iron man / superhuman strength with engineering
leverage and constraints." Lift more than you can unaided, stay flexible and
light, and stay safe. Order of tools: leverage and stored energy first,
motors only where they can't do the job.

All numbers below come from `python3 scripts/assist_curve.py`, which runs the
fictional example body in `data/example_body.json` (70 kg, 0.55 m torso).
They are **example data**, not Ben's measurements and not test results.

## Words used once

- **Torque (moment):** turning force = force x perpendicular distance (Nm).
- **Moment arm / lever:** that perpendicular distance. A longer lever turns
  the same force into more torque.
- **L5/S1:** the lowest joint of the spine, where lifting stress peaks.
- **Extensor:** the back and hip muscles that pull you upright.
- **Stored energy:** a stretched spring holds energy and gives it back.
- **Clutch:** a lock that turns the spring on or off.
- **Interface:** where the suit touches you (straps, pads). Skin and soft
  tissue limit how hard it can push.

## 1. First joint: hips and low back, lifting and bending

Pick the hip/low-back joint first because:

- It carries the biggest load in daily lifting. A 15 kg box at a 90 deg stoop
  needs about 241 Nm at the hip in the model, about 2x the 129 Nm the repo
  computes for a full push-up at the shoulders.
- It is the best-studied wearable target: two systematic reviews cover 30+
  back-support devices (Kermavnar et al. 2021; Ali et al. 2021).
- It reuses the repo's planar lever directly. The trunk is one rigid link
  pivoting at the hip, like the push-up body pivoting at the feet.
- Its pads sit on the chest and thighs, which take load far better than
  hands, shoulders or knees.

## 2. Load path and load cases

**Load path:** box -> hands -> arms -> trunk -> hip/L5-S1 -> pelvis -> legs ->
floor. The suit adds a parallel path: **chest pad -> rigid strut -> hip spring
-> thigh pads**. That path ends at the thighs, not the floor, so every newton
the suit gives also passes through his skin at the pads. That is the main
limit (see section 3).

**Model** (`biomech/suit.py`): head, arms and trunk weigh 0.678 x body mass
with their centre of mass at 0.626 of hip-to-shoulder length (Winter, Table
4.1). Moment = weight x lever x sin(trunk lean) + box weight x reach. Spine
compression = moment / 0.05 m (the usual one-muscle shortcut; McGill & Norman
1987 show a 7.5 cm arm can fit better, so read compression **relative**, not
absolute) + weight along the spine.

Example body, 15 kg box, v0 spring (section 5):

| Load case | Hip / trunk deg | Back moment unaided | Suit assist | Box feels like | L5/S1 compression, unaided -> suit |
|---|---:|---:|---:|---:|---:|
| Standing | 0 / 0 | 0 Nm | 0 | 15 kg | 613 -> 613 N |
| Stoop, half way | 45 / 45 | 171 Nm | 24 Nm | 8.7 kg | 3845 -> 3362 N |
| **Stoop, bottom (worst moment)** | 90 / 90 | **241 Nm** | 44 Nm | **6.8 kg** | 4825 -> 3940 N |
| Squat lift (box 0.60 m out) | 135 / 45 | 202 Nm | 44 Nm | 7.5 kg | 4466 -> 3581 N |
| **Squat, upright trunk (worst for the suit)** | 120 / 30 | 80 Nm (body only) | 44 Nm (max allowed 48) | — | sizes the spring |
| **Sitting, clutch on (fault case)** | 90 / 5 | 14 Nm | 44 Nm | n/a | suit pushes him backward |

Compression: NIOSH uses 3400 N at L5/S1 as its risk line (Waters et al. 1993).
In this crude model a 15 kg stoop lift crosses it unaided, and the suit cuts
the estimate about 18%. It does not get the lift under the line by itself.

**Worst case sizes the part.** The stoop bottom has the biggest back moment.
But the **squat with an upright trunk** limits the spring: the hip bends 120
deg (so the spring is stretched), while the trunk leans only 30 deg (so the
upper body weighs little against it). An unlimited spring there pushes the
trunk backward harder than gravity pulls it forward. Two rules follow, and
`check_design()` enforces them:

1. **No recoil:** assist stays under 60% of the upper body's own gravity
   moment in every clutch-on pose. If he drops the box, the suit can't snap
   him upright. (60% is my margin choice, provisional.)
2. **Torque plateau:** a stretch-limiter strap stops the spring at 70 deg, so
   assist tops out at 44 Nm and never grows in a deep squat.

**Sitting is a fault case.** Hip at 90 deg with an upright trunk means any hip
spring pushes him back into the chair. The clutch must be off to sit. The test
suite keeps this pose as a known-bad case the check must always flag.

## 3. Amplification target and what limits it

**v0 target (passive frame): a 15 kg lift feels like about 7 kg at the bottom
of the lift** (6.8 kg at a 90 deg stoop, 7.5 kg in a squat lift, 8.7 kg half
way up, no help when upright). That is about an 18% cut in back moment with
the box, 28% with no box.

Three limits, tightest first:

1. **Body interface.** Men in Kozinc et al. 2021 first felt discomfort at
   230 +/- 45 N from an exoskeleton chest strap. I cap the chest pad at 185 N
   (mean minus one SD). Max torque = pad force x lever length, so:
   - Soft straps over the shoulders (lever about 0.15 m): about **28 Nm**.
   - Rigid strut to a chest pad (lever 0.44 m): about **81 Nm**.
   **The lever is the amplifier.** It nearly triples what skin will accept.
   Thigh pads see torque / 0.30 m, so 147 N total. They need at least 150 cm2
   each (about 5 kPa), well under the 16-34 kPa where squeezing the thigh gets
   uncomfortable (Kermavnar et al. 2018 review).
2. **Energy.** A spring can only return energy you put in by bending down. The
   v0 spring stores about 21 J. One 90 deg stoop lift of a 15 kg box 0.5 m
   needs about 234 J (160 J for the upper body, 74 J for the box). Passive
   springs reshape torque; they cannot add work. More than this needs a motor.
3. **Power and mass (active only).** Holding the 81 Nm interface cap through
   a lift at 90 deg per second (an example speed) needs about 130 W at the hip,
   plus battery, motor and gearbox mass. Published active back exos weigh 3 kg
   (HAL lumbar) to 11.6-16.5 kg (Robo-Mate; Twente/Delft dual-joint).

**Ceiling for any suit that ends at the thighs:** about 81 Nm, so roughly
**"30 kg feels like 15 kg"** at the bottom of a stoop. Past that, the load path
must go through rigid legs to the floor, which brings a big jump in mass, cost
and fall risk. That option is parked.

## 4. Concepts

| | A. Soft elastic suit | **B. Rigid-lever spring frame** | C. B + hip motor |
|---|---|---|---|
| Main idea | Bands from a shoulder harness to thigh sleeves, plus an on/off buckle (like HeroWear Apex) | A strut from a chest pad to a hip cam spring, with thigh pads and a manual clutch (like Laevo) | B's frame with a geared motor at each hip, an IMU and a controller |
| Peak assist (interface cap) | ~28 Nm | 44 Nm v0, ~81 Nm ceiling | ~81 Nm, held through the whole lift |
| 15 kg box feels like (stoop bottom) | ~10 kg | ~7 kg (v0) | 30 kg feels like ~15 kg |
| Mass | ~1-1.5 kg (Apex 1.54 kg) | ~2-2.5 kg (Laevo 2.3 kg) | 3 kg+ (published 3-16.5 kg) |
| Rough cost (estimate) | $40-80 | $60-120 | $300-800+ |
| ROM impact | None when off. On, resists sitting | Low when off. On, blocks sitting; struts limit twisting unless the chest pad swivels | Can be software-free, but it is heavy and the motor drag adds up |
| Safety | Band tension runs along the spine and adds some compression. A snapped band whips | No recoil by design (cap + plateau). Fails to "off". Springs are boxed on the frame | Motor can drive past range: needs hard stops, current limit, e-stop, no auto-restart |
| Buildability | High: sewing, webbing, bands | High-medium: 3D prints, flat aluminium bar, bearings | Low for a first build: motor driver, battery, control code |

**Literature check** (EMG = muscle electrical activity):
- Passive back exos cut back-muscle EMG by 18% on average in lifting and 36%
  in static bending (Kermavnar et al. 2021).
- A soft band garment cut it 23-43% in leaning and 14-16% in squat lifts, with
  peak band forces of about 27% of body weight (Lamers et al. 2018).
- Active devices reported 12-15% (Robo-Mate), and an active dual-joint exo cut
  L5/S1 compression by 5.5-9.3%.
- So far, motors haven't beaten good passive designs on back load. They mainly
  add help through the full range.

## 5. Pick: B, the rigid-lever spring frame (my pick; Ben decides)

**Why B:**
- It follows Ben's order: **leverage first** (the chest strut is the
  amplifier), then **stored energy** (the hip spring), then **a motor later**
  (C bolts onto B's hip axis when the frame is proven).
- It gets the most strength per kg and per dollar inside the skin limit.
- It fails safe: if the clutch pin falls out, there is no assist.
- A gives more flexibility for less strength. That trade is a taste call for Ben.

**v0 sizing** (`scripts/assist_curve.py`):
- 7200 N/m total spring on 0.08 m cams.
- Slack below 15 deg hip flexion, so it has no effect standing or walking slowly.
- Stretch limiter at 70 deg, so the plateau is 44 Nm (max spring tension
  553 N, inside the frame, not on skin).
- Chest pad 101 N, thigh pads 147 N. Safety check: pass.

**Safety rules (hard):**
- No assist below 15 deg.
- Assist under 60% of own trunk moment.
- A mechanical stop at full hip extension.
- One-handed clutch off and belt release in under 2 s.
- Springs boxed so a break can't hit the face.
- Clutch off to sit.
- Stop on any discomfort (same rule as the push model).
- Not for use with existing back pain without a clinician.
- v0 testing uses loads Ben already lifts unaided. No max lifts until a
  measured curve matches the model.

### Smallest testable prototype (no purchases made)

| Part | Rough cost (estimate, not quotes) |
|---|---:|
| Padded hip belt (lifting or old backpack belt) | $0-25 |
| 2x 25x3 mm aluminium flat bar, 1 m (struts) | $10-15 |
| Chest pad: printed plate, 10 mm foam, strap, swivel | $5-10 |
| 2x thigh pads >=150 cm2: printed shell, foam, velcro | $10-15 |
| 2x hip cam + hinge: PETG prints, 608 bearings, M8 bolts, end stop | $5-10 |
| Springs: heavy latex loop bands (2 per side) + limiter strap | $15-30 |
| Clutch: printed pin + pawl per side, pull lanyard | ~$2 |
| Test kit: 50 kg digital luggage scale; phone inclinometer app | $10-15 |
| **Total** | **~$60-120** |
| Optional: hobby EMG sensor for proof of reduced muscle load | +~$40 |

### Tests that prove it works

1. **Bench curve (no body):** pull the cam round with the luggage scale at
   0/15/30/45/60/70/90 deg. Pass: torque within 20% of the script, zero at
   15 deg and below, flat past 70 deg.
2. **Amplification (main proof):** static lean at 60 and 90 deg holding 5 kg,
   clutch off vs on, randomised order, 3 trials each. EMG on the low back if
   the sensor is bought. Pass: at least 15% lower back-muscle EMG on (below
   the 18-36% passive average), and Ben rates the box lighter blind.
3. **Range of motion:** phone on sternum and thigh. Measure max bend, deep
   squat, sitting, stairs and 5 min of walking with no suit, clutch off and
   clutch on. Pass: clutch off loses 5 deg or less in any motion. Published
   rigid exos lost about 13 deg (SPEXOR).
4. **Comfort:** wear it 30 min with the clutch off, then do 10 lifts with it
   on. Pass: pad discomfort 3/10 or less, no marks after 15 min.
5. **Safety:** clutch off one-handed under full spring load in under 2 s.
   Belt release in under 2 s. On the bench (eye protection, nobody in line),
   cut a band at full stretch: the cover contains it.

Then replace the example body with Ben's lidar-measured torso and mass and
re-run the script.

## Sources

- Kermavnar T, de Vries AW, de Looze MP, O'Sullivan LW (2021). Effects of
  industrial back-support exoskeletons on body loading and user experience:
  an updated systematic review. *Ergonomics* 64(6):685-711.
  doi:10.1080/00140139.2020.1870162. Mean figures as quoted in "Effectiveness of
  soft versus rigid back-support exoskeletons during a lifting task" (2021),
  *IJERPH* 18(15):8062.
- Ali A, Fontanari V, Schmoelz W, Agrawal SK (2021). Systematic review of
  back-support exoskeletons and soft robotic suits. *Front. Bioeng.
  Biotechnol.* 9:765257. Device masses: Laevo 2.3 kg, Apex 1.54 kg, HAL
  lumbar 3 kg, Robo-Mate 11.6 kg, SPEXOR -13 deg ROM.
- Lamers EP, Yang AJ, Zelik KE (2018). Feasibility of a biomechanically-
  assistive garment to reduce low back loading during leaning and lifting.
  *IEEE TBME* 65(8):1674-1680.
- Huysamen K et al. (2018). Assessment of an active industrial exoskeleton to
  aid dynamic lifting and lowering manual handling tasks. *Applied
  Ergonomics* 68:125-131.
- Dual-joint active back-support exoskeleton, varied assistance levels (2025).
  *Ergonomics*. doi:10.1080/00140139.2025.2466030.
- Kozinc Ž, Babič J, Šarabon N (2021). Human pressure tolerance and effects
  of different padding materials with implications for development of
  exoskeletons. *Applied Ergonomics* 93:103379.
- Kermavnar T et al. (2018). Computerized cuff pressure algometry as guidance
  for circumferential tissue compression for wearable soft robotic
  applications: a systematic review. *Soft Robotics* 5(1):1-16.
- Winter DA. *Biomechanics and Motor Control of Human Movement*, 4th ed.,
  Table 4.1.
- McGill SM, Norman RW (1987). Effects of an anatomically detailed erector
  spinae model on L4/L5 disc compression and shear. *J Biomech* 20(6):591-600.
- Waters TR, Putz-Anderson V, Garg A, Fine LJ (1993). Revised NIOSH equation
  for the design and evaluation of manual lifting tasks. *Ergonomics*
  36(7):749-776.
