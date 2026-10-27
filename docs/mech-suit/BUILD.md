# Mech suit v0 build: concept B, rigid-lever gas-strut frame

**Chosen by Ben on Oct 24, 2026, 7:47 PM PT.** This is the smallest build that
can pass the five acceptance tests at the end. Nothing has been bought. Every
price is an estimate from a listing seen on Oct 24, 2026.

**All body numbers are the example body** (`data/example_body.json`: 70 kg,
torso 0.55 m, thigh 0.45 m), not Ben's. Once Ben's lidar measurements exist,
put them in a private copy of that file and run
`python3 scripts/assist_curve.py path/to/ben_body.json`. Then rescale the
lengths marked *(body)* and re-run the safety check before cutting anything.

## How it works

Each side has two aluminium bars joined by a hip pivot at the bony bump on the
side of the hip (the greater trochanter):

- The **trunk strut** runs up to a chest pad.
- The **thigh bar** runs down to a thigh pad.

A **gas strut** pushes between a point 0.27 m up the trunk strut and a short
**crank** on the thigh bar. When you bend forward past about 29 deg, the strut
gets shorter and pushes back. That makes a torque that helps the hips and back
straighten up.

The torque reaches the body only through the chest pad and the thigh pads.
The long bars are the lever that keeps those pad forces low.

## Key dimensions, each sized from its worst case

| Dimension | Value | Sized by (worst case) |
|---|---:|---|
| Pivot to chest-pad centre *(body: 0.8 x torso)* | **0.44 m** | Chest pad force stays at or under 185 N (max 124 N at 81 deg) |
| Pivot to thigh-pad centre *(body: 0.67 x thigh)* | **0.30 m** | Thigh pressure stays under 16 kPa (max 91 N per pad, about 5 kPa) |
| Gas strut top mount, up the trunk strut | **0.27 m** | Most torque (54 Nm at 90 deg) with no recoil in the 120/30 deg upright squat (37 of 48 Nm allowed) |
| Crank radius (replaces the old "pulley radius") | **60 mm** | Same optimisation. Strut never bottoms out (213 mm at 135 deg vs 206 mm fully compressed) |
| Crank angle from the trunk strut, standing | **150 deg** (30 deg forward of the thigh bar) | Torque falls in a deep squat, where the trunk can't resist it |
| Lost-motion slot (replaces "band preload") | **19 mm** + 3 mm rubber bumper | Strut idle below 29 deg, so walking and standing feel nothing |
| Gas strut (replaces "band spec") | **400 N (90 lb), 12 in extended, about 8.1 in compressed, 10 mm ball ends**, one per side | Max strut force 512 N at 135 deg, assuming a 30% force rise over the stroke |
| Stretch-limit strap | **Removed** | It can't work (see the SPEC correction). The crank geometry does the job instead |
| Hip extension stop | -20 deg | Frame can't fold backward; walking needs about 10-15 deg |
| Hip flexion stop | 140 deg | Above anatomical range. Stops the crank going past its dead point at 150 deg |

The script prints the whole torque curve and checks it against the safety
rules (no recoil, chest pad limit, never blocking motion, idle when upright).

**Bar check (6061 aluminium, 1/8 x 1-1/2 in, set on edge so the 1.5 in width
does the bending):**
- The thigh bar takes the most bending: 27 Nm per side at the pivot, giving a
  stress of 36 MPa. Bolt holes multiply stress by about 3, to 107 MPa. Typical
  6061-T6 yields at 276 MPa, so the margin against yielding is about **2.6**.
- The trunk strut is squeezed lengthwise by the gas strut (up to 512 N) over
  0.27 m. Buckling sideways is its weak mode: it buckles at about 950 N if the
  ends act as pins, or about 1.9 kN when clamped in the hub. That gives a
  margin of 1.9 to 3.8.
- If a bar bows sideways in bench test 1, stop and double the bar.

## 3D-printed parts

Print everything in **PETG** with 5 perimeters, 40% gyroid infill and 0.2 mm
layers. Lay each part flat so the layers don't split along the main load.
Sizes are rough until CAD.

| Part (qty) | What it does | Rough size | Load it carries |
|---|---|---|---|
| Hip hub (2) | Holds two 608 bearings on the M8 pivot. Clamps the trunk strut's lower end (3x M5). Holds the stop faces | 70 x 50 x 24 mm | Pivot reaction up to ~600 N |
| Crank plate (2) | Clamps the thigh bar's top (3x M5). Carries the M8 pivot shaft. Holds the lower ball stud 60 mm from the pivot, 30 deg forward | 110 x 60 x 12 mm | 512 N at the ball stud (~15 Nm bending in the plate) |
| Slot link (2) | Holds the strut's top ball stud in a 19 mm slot with a bumper. Pinned to the trunk strut by the ball-lock pin (this is the **clutch**) | 60 x 30 x 20 mm | 512 N through the slot end |
| Chest plate (1) | Curved pad shell, lined with 10 mm foam | 250 x 120 x 4 mm | 124 N spread over ~300 cm2 (~4 kPa) |
| Chest swivel clip (2) | Joins each trunk strut top to the chest plate on an M5 pivot, so twisting isn't blocked | 50 x 30 x 15 mm | 62 N each |
| Thigh pad shell (2) | Curved shell with a slot for ±20 mm sliding along the thigh bar (absorbs pivot misalignment). Strap slots for 2 in straps | 150 x 120 x 3 mm | 91 N each over 180 cm2 (~5 kPa) |
| Belt bracket (2) | Holds each hip hub on the 2 in belt at trochanter height | 70 x 60 x 6 mm | Frame weight and positioning only; the torque closes through the pads |

Filament use: roughly 300-400 g (estimate).

## Parts list (BOM)

All prices are estimates. **Nothing has been purchased.** "Link checked" means
I opened the listing or read it in search results on Oct 24, 2026; prices and
stock change.

| # | Item | Qty | Est. price | Link | Notes |
|---|---|---:|---:|---|---|
| 1 | ARANA C1615056 gas struts, 12 in, 90 lb/400 N, pair | 1 pair | $18.99 | [Amazon](https://www.amazon.com/ARANA-15-inch-Gas-Struts/dp/B0C33TMK3V) | Price from search; page blocked my fetch. Confirm 400 N, ~8.1 in compressed, 10 mm ball sockets |
| 2 | KEMANI 10 mm ball studs, M8, 8-pack | 1 | $11.69 | [Amazon](https://www.amazon.com/KEMANI-4pcs10mm-Fittings-Fitting-Hardware/dp/B0CX4TV59K) | 4 used |
| 3 | VXCICC 8 mm ball-lock quick-release pins with lanyard, 2-pack | 1 | $12.99 | [Amazon](https://www.amazon.com/VXCICC-Stainless-Release-Diameter-Locking/dp/B0D3QDSGVT) | The clutch. 20 mm grip length |
| 4 | AC/DC 6061 aluminium flat bar, 1/8 x 1-1/2 x 36 in | 2 | $55.54 ($27.77 ea) | [Amazon](https://www.amazon.com/Supply-Aluminum-Stock-Solid-1-500/dp/B09SR86GCH) | Each bar gives one 500 mm trunk strut and one 350 mm thigh bar. Temper not stated; ask for T6. Home Depot's [6063-T5 bar](https://www.homedepot.com/p/Everbilt-1-1-2-in-x-3-ft-1-8-in-Thick-Aluminum-Flat-Bar-6215/332735519) costs $15.58 but is weaker (margin ~1.4); not recommended |
| 5 | Donepart 608-2RS bearings, 10-pack | 1 | $7.78 | [Amazon](https://www.amazon.com/dp/B07WZTYG3M) | 4 used |
| 6 | uxcell M8 x 50 mm stainless bolts, nuts, washers, 6 sets | 1 | $8.89 | [Amazon](https://www.amazon.com/uxcell-Screws-Washers-Stainless-Hexagon/dp/B098D7X9GF) | Hip pivots. Add M8 nylon lock nuts if the kit lacks them |
| 7 | M5/M6/M8/M10 stainless socket-cap assortment, 365 pc | 1 | $13.92 | [Amazon](https://www.amazon.com/PGMJ-1500Pcs-Washers-Stainless-Assortment/dp/B0CGRJ4LGN) | About 20 M5 bolts used. Skip it if the makerspace has M5s |
| 8 | The Foamory EVA foam, 10 mm, 14 x 39 in | 1 | $23.99 | [Amazon](https://www.amazon.com/EVA-Foam-Cosplay-Density-Foamory/dp/B08YXYBZQ7) | Pad liners. Page opened and price confirmed |
| 9 | Hook-and-loop cinch straps, 2 x 24 in, 6-pack | 1 | $9.99 | [Amazon](https://www.amazon.com/HUAHAITGCH-Fastening-Adjustable-Multi-Purpose-Management/dp/B0F8HJYPML) | 4 for the thighs, 1-2 for the chest |
| 10 | FireForce universal 2 in backpack waist belt | 1 | ~$20 (price not shown) | [Amazon](https://www.amazon.com/Fire-Force-Backpack-Universal-Military/dp/B00UACXY06) | Any padded 2 in hip belt works |
| 11 | Overture PETG 1.75 mm, 1 kg | 1 | $14.69 | [Amazon](https://www.amazon.com/OVERTURE-Filament-Consumables-Dimensional-Accuracy/dp/B07PGYHYV8) | Skip it if the makerspace supplies filament |
| 12 | Etekcity luggage scale, 110 lb | 1 | $9.86 | [Amazon](https://www.amazon.com/Etekcity-Luggage-Scale-Travel-Essentials/dp/B082LYC2TN) | For bench test 1 |
| | **Total** | | **≈ $208.33** | | Before tax and shipping. Without items 6, 7 and 11 (makerspace stock): ≈ $171 |
| opt | Hobby EMG sensor | 1 | ~$40 | — | Only for the main proof in test 2; not picked yet |

Also needed (makerspace): hacksaw or bandsaw, file, a drill with 5.2 and 8.2 mm
bits, vise, contact cement, a 3 mm rubber sheet scrap for the slot bumpers,
and a phone inclinometer app.

## Build order (beginner steps)

**Safety first:**
- Wear eye protection when cutting and drilling.
- Never heat, drill, crush or take apart a gas strut. It is pressurised.
- Keep fingers out of the pivot and crank while anything is under load.

1. **Measure.** Measure your hip-to-shoulder length, thigh length and mass,
   and find the bony bump on the side of each hip. Put the numbers in a
   private copy of `data/example_body.json` (don't commit it) and run the
   script. If the safety check fails, stop and re-size first.
2. **Print** the seven part types listed above.
3. **Cut the bars.** Cut each 36 in bar into a 500 mm trunk strut and a 350 mm
   thigh bar. File the cut ends round and break every sharp edge.
4. **Drill.** Measure each hole from the pivot end:
   - Trunk strut: three 5.2 mm hub holes at 15, 35 and 55 mm; one 8.2 mm
     clutch-pin hole at 270 mm; three 5.2 mm chest-clip holes at 420, 440 and
     460 mm (these adjust the chest lever).
   - Thigh bar: 5.2 mm holes at 15, 35, 55, 290 and 310 mm.
   - Deburr every hole.
5. **Bend** each trunk strut gently in a vise across its thin direction, about
   15-20 deg in total between 150 and 250 mm, so it follows the side of your
   ribs toward the chest. Never bend it across the 1.5 in width.
6. **Hip pivots.** Press two 608 bearings into each hip hub. Slide the M8
   pivot through the crank plate and bearings, and tighten the nylon lock nut
   until it has no play but still turns freely.
7. **Bolt the bars on** with 3x M5 each: trunk strut to hip hub, thigh bar to
   crank plate. Swing each joint by hand: it should be free from -20 deg to
   140 deg and stop at both ends.
8. **Fit the gas struts** (rod end down). Screw a ball stud into each crank
   plate at the 60 mm hole and into each slot link. Snap the strut ends onto
   the studs. Pin each slot link to its trunk strut at 270 mm with the
   ball-lock pin.
9. **Run bench test 1** below before the frame ever goes on a body.
10. **Make the pads.** Glue foam to the chest plate and thigh shells. Fit the
    chest swivel clips and the thigh shells on their slots. Thread the straps.
11. **Fit the belt** brackets so the pivots sit on the bony bumps at the hips.
12. **First wear with the clutch off** (pins out). Walk, sit, squat and take
    stairs. Nothing should rub or catch.
13. Run tests 2-5, using only loads you already lift without the suit.

## Acceptance tests (from SPEC.md)

- [ ] **1. Bench curve.** Clamp the trunk strut. Hook the luggage scale on
  the thigh bar 0.30 m from the pivot and read it at 30, 45, 60, 90, 110 and
  135 deg. Torque per side = reading (N) x 0.30 m. Pass: within 20% of half
  the script's total, zero at 25 deg and below, and no bottoming out at 135 deg.
- [ ] **2. Amplification (main proof).** Static lean at 60 and 90 deg holding
  5 kg, clutch off vs on, random order, 3 trials each. Use EMG on the low back
  if bought. Pass: at least 15% lower back-muscle EMG with the clutch on, and
  Ben rates the box lighter without knowing which trial is which.
- [ ] **3. Range of motion.** Phone on the sternum and thigh. Measure max
  bend, deep squat, sitting, stairs and 5 min of walking three ways: no suit,
  clutch off, clutch on. Pass: clutch off loses 5 deg or less in any motion.
- [ ] **4. Comfort.** Wear it 30 min with the clutch off, then do 10 lifts
  with it on. Pass: pad discomfort 3/10 or less, no marks after 15 min.
- [ ] **5. Safety.** The clutch pin comes out one-handed in under 2 s while
  standing (pin unloaded). Belt and chest buckles release one-handed in under
  2 s. Dropping a 5 kg box at the stoop bottom does not throw the trunk
  upright. Sitting with the clutch on is never done (known-bad case).

## Open items before buying

- The ARANA page blocked my fetch, so its price and compressed length come
  from search results only. Check them, because the geometry has just 4 mm
  of spare stroke.
- The 30% gas-strut force rise is an assumption. Bench test 1 measures it.
  Put the real number in `V0_STRUT` in `biomech/suit.py` and re-run the
  script.
- The aluminium temper isn't stated on the listing.
- Dimensions use the example body until Ben's lidar measurements arrive.
