"""Acceptance checks written before implementation.

Failure inventory: incorrect force projection/units/bilateral convention; a
hard-coded rank; unsafe progress despite effort, missed reps, or discomfort;
catalogue gaps outside 10–20%, nominal heights inconsistent with poses;
large jumps hidden from the user; no easier/harder move; malformed JSON,
unknown IDs, nonfinite/bool numbers, impossible geometry, unsorted dates;
CLI tracebacks or source-file writes; a beginner unable to recover and finish.
"""

import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from biomech.core import lever_load, load_moves, rank_moves, recommend
from biomech.measurements import BodyDimensions, load_body, load_ply
from biomech.sessions import Session, load_sessions


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUSH_STEPS = [
    "wall-push-up", "high-rail-push-up", "rail-push-up",
    "counter-tucked-push-up", "counter-forward-push-up", "incline-push-up",
    "knee-push-up", "bench-push-up", "step-push-up", "full-push-up",
]


class FrameworkAcceptance(unittest.TestCase):
    def setUp(self):
        self.body = load_body(DATA / "example_body.json")
        self.moves = load_moves(DATA / "moves.json")
        self.by_id = {move.id: move for move in self.moves}

    def session(self, move_id="wall-push-up", reps=8, rpe=7,
                discomfort=False, discomfort_notes=""):
        return Session("2026-10-19", move_id, reps, rpe,
                       discomfort, discomfort_notes)

    def decision(self, session, moves=None):
        return recommend(session, self.moves if moves is None else moves,
                         self.body, 150)

    def cli(self, log_path, *extra):
        # A caller outside the checkout must be able to use explicit paths.
        env = dict(os.environ, PYTHONPATH=str(ROOT))
        return subprocess.run(
            [sys.executable, "-m", "biomech", "--body",
             str(DATA / "example_body.json"), "--moves", str(DATA / "moves.json"),
             "--log", str(log_path), "--strength-reference", "150", *extra],
            cwd=log_path.parent, env=env, text=True, capture_output=True,
            timeout=10, check=False)

    def test_hand_calculations(self):
        # Independent hand calculation, SI units, both shoulders together:
        # m=70, g=9.81; upper arm=.30, forearm=.25; alpha=-60, beta=60.
        # d=.30*cos(-60)+.25*cos(0)=.15+.25=.40 m.
        # Full: S=.55+.45+.45=1.45, c=.60*S=.87, H=S+d=1.85.
        # F=70*9.81*.87/1.85=322.9346 N; tau=F*.40=129.1738 Nm.
        # Table: alpha=-83, beta=60; d=.2666870, theta=38.169472.
        # F=597.429*cos(theta)/(1.45+d)=273.6029; tau=72.9663 Nm.
        # Wall: cos(75)=.2588190; F=83.5816; tau=33.4326 Nm.
        # Knee: S=.55+.45=1, c=.55; effective mass=.8*70=56 kg.
        # F=56*9.81*.55/1.40=215.82 N; tau=86.328 Nm.
        expected = {
            # ID: (moment arm in m, total force in N, bilateral torque in Nm).
            "wall-push-up": (.40, 83.5816, 33.4326),
            "high-rail-push-up": (.2870176, 134.4141, 38.5792),
            "rail-push-up": (.2527237, 180.9993, 45.7428),
            "counter-tucked-push-up": (.2165064, 249.6546, 54.0518),
            "counter-forward-push-up": (.2527237, 251.0640, 63.4498),
            "incline-push-up": (.2666870, 273.6029, 72.9663),
            "knee-push-up": (.40, 215.82, 86.328),
            "bench-push-up": (.3191272, 304.1049, 97.0481),
            "step-push-up": (.3488080, 315.6686, 110.1077),
            "full-push-up": (.40, 322.9346, 129.1738),
        }
        for move_id, (arm, force, torque) in expected.items():
            with self.subTest(move_id=move_id):
                load = lever_load(self.by_id[move_id], self.body)
                self.assertAlmostEqual(load.moment_arm_m, arm, places=6)
                self.assertAlmostEqual(load.hand_force_n, force, delta=.0001)
                self.assertAlmostEqual(load.torque_nm, torque, delta=.0001)

    def test_body_and_joint_geometry_change_the_load(self):
        heavier = BodyDimensions(140, .55, .45, .45, .30, .25)
        self.assertAlmostEqual(
            lever_load(self.by_id["full-push-up"], heavier).torque_nm,
            258.3477, delta=.01)
        raw = json.loads((DATA / "moves.json").read_text())
        raw[-1]["geometry"]["upper_arm_angle_deg"] = 0
        raw[-1]["geometry"]["elbow_angle_deg"] = 0
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "moves.json"
            source.write_text(json.dumps(raw))
            # d=.30+.25=.55; tau=686.7*.87/(1.45+.55)*.55=164.2900.
            changed = lever_load(load_moves(source)[-1], self.body)
        self.assertAlmostEqual(changed.torque_nm, 164.289975, delta=.01)

    def test_push_ordering_and_strength_reference(self):
        ranked = rank_moves(list(reversed(self.moves)), self.body, 150, "push")
        self.assertEqual([item.move.id for item in ranked], PUSH_STEPS)
        for left, right in zip(ranked, ranked[1:]):
            self.assertLess(left.relative_torque, right.relative_torque)
        self.assertAlmostEqual(ranked[-1].relative_torque, .8611589, places=6)
        stronger = rank_moves(self.moves, self.body, 300, "push")
        self.assertAlmostEqual(stronger[-1].relative_torque, .4305795, places=6)

    def test_progress_in_target_band(self):
        result = self.decision(self.session("incline-push-up", reps=9))
        self.assertEqual((result.action, result.move_id, result.flagged_jump),
                         ("progress", "knee-push-up", False))
        self.assertAlmostEqual(result.jump_fraction, .1831210, places=6)
        self.assertIn("18.3%", result.reason)

    def test_large_jump_is_closest_and_flagged(self):
        sparse = [self.by_id[move_id] for move_id in
                  ("wall-push-up", "full-push-up")]
        result = self.decision(self.session(), sparse)
        self.assertEqual((result.action, result.move_id, result.flagged_jump),
                         ("progress", "full-push-up", True))
        # 1/cos(75) - 1: sparse catalogues must still flag a large jump.
        self.assertAlmostEqual(result.jump_fraction, 2.8637033, places=5)
        self.assertIn("outside", result.reason)

    def test_hold_and_top_of_pattern(self):
        for session, reason in [
            (self.session(rpe=7.1), "RPE"),
            (self.session(reps=7, rpe=5), "rep target"),
            (self.session("full-push-up"), "top"),
        ]:
            with self.subTest(reason=reason):
                result = self.decision(session)
                self.assertEqual((result.action, result.move_id),
                                 ("hold", session.move_id))
                self.assertIn(reason, result.reason)

    def test_discomfort_overrides_performance_and_bottom_stops(self):
        result = self.decision(self.session(
            "knee-push-up", reps=12, rpe=2, discomfort=True,
            discomfort_notes="Wrist discomfort"))
        self.assertEqual((result.action, result.move_id),
                         ("regress", "incline-push-up"))
        self.assertIn("Discomfort", result.reason)
        bottom = self.decision(self.session(
            discomfort=True, discomfort_notes="Shoulder discomfort"))
        self.assertEqual((bottom.action, bottom.move_id), ("regress", None))
        self.assertIn("stop", bottom.reason.lower())

    def test_band_selection_skips_tiny_step_and_flags_small_fallback(self):
        raw = json.loads((DATA / "moves.json").read_text())[-1]
        variants = []
        for move_id, mass_fraction in [("base", .5), ("tiny", .525),
                                       ("ideal", .575), ("large", .7)]:
            item = copy.deepcopy(raw)
            item["id"] = move_id
            item["geometry"]["mass_fraction"] = mass_fraction
            variants.append(item)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "moves.json"
            source.write_text(json.dumps(variants))
            moves = load_moves(source)
        result = self.decision(self.session("base"), moves)
        self.assertEqual((result.move_id, result.flagged_jump), ("ideal", False))
        fallback = self.decision(self.session("base"), moves[:2])
        self.assertEqual((fallback.move_id, fallback.flagged_jump), ("tiny", True))
        self.assertAlmostEqual(fallback.jump_fraction, .05)

    def test_example_log_and_body_round_trip(self):
        self.assertEqual(self.body.mass_kg, 70)
        sessions = load_sessions(DATA / "example_session_log.json", self.moves)
        self.assertEqual(sessions[-1].move_id, "incline-push-up")
        self.assertEqual(self.decision(sessions[-1]).move_id, "knee-push-up")
        with self.assertRaises(NotImplementedError):
            load_ply(Path("not-parsed.ply"))

    def test_log_validation(self):
        good = {
            "date": "2026-10-19", "move_id": "wall-push-up", "reps": 8,
            "rpe": 7, "discomfort": False, "discomfort_notes": "",
        }
        bad_fields = {
            "date": ["2026-02-30", "20261019", "yesterday", 10],
            "move_id": ["unknown", "", None],
            "reps": [-1, 1.5, True, "8"],
            "rpe": [0, 11, True, float("nan"), float("inf")],
            "discomfort": ["false", 0, None],
            "discomfort_notes": [12, None],
        }
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "log.json"
            for field, values in bad_fields.items():
                for value in values:
                    with self.subTest(field=field, value=value):
                        item = dict(good, **{field: value})
                        source.write_text(json.dumps([item]))
                        with self.assertRaises(ValueError):
                            load_sessions(source, self.moves)
            invalid_logs = [
                {}, [None], [dict(good, extra="typo")],
                [{key: value for key, value in good.items() if key != "reps"}],
                [dict(good, discomfort=True)],
                [good, dict(good, date="2026-10-18")],
            ]
            for value in invalid_logs:
                source.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    load_sessions(source, self.moves)
            source.write_text("broken json")
            with self.assertRaises(ValueError):
                load_sessions(source, self.moves)
            source.write_text("[]")
            self.assertEqual(load_sessions(source, self.moves), [])

    def test_measurement_move_and_reference_validation(self):
        body = json.loads((DATA / "example_body.json").read_text())
        moves = json.loads((DATA / "moves.json").read_text())
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.json"
            for field in body:
                for value in [0, -1, True, float("inf"), "0.5", None]:
                    source.write_text(json.dumps(dict(body, **{field: value})))
                    with self.subTest(field=field, value=value):
                        with self.assertRaises(ValueError):
                            load_body(source)
            for invalid in [[], {}, dict(body, unexpected=1)]:
                source.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    load_body(source)
            bad_moves = [[], {}, [moves[0], moves[0]], [None]]
            for field, value in [
                ("id", ""), ("name", ""), ("pattern", ""),
                ("muscle_groups", []), ("muscle_groups", "chest"),
                ("muscle_groups", [""]), ("rep_target", 0),
                ("rep_target", True), ("geometry", {}), ("unexpected", 1),
            ]:
                bad_moves.append([dict(moves[0], **{field: value})])
            for field, value in [
                ("body_angle_deg", 90), ("body_angle_deg", -1),
                ("mass_fraction", 0), ("mass_fraction", 1.1),
                ("com_fraction", 1.1), ("com_fraction", float("nan")),
                ("support_segments", []), ("support_segments", ["unknown"]),
                ("support_segments", ["torso_m", "torso_m"]),
                ("upper_arm_angle_deg", 181), ("elbow_angle_deg", True),
                ("upper_arm_angle_deg", 180),
            ]:
                item = copy.deepcopy(moves[0])
                item["geometry"][field] = value
                bad_moves.append([item])
            for invalid in bad_moves:
                source.write_text(json.dumps(invalid))
                with self.subTest(invalid=invalid):
                    with self.assertRaises(ValueError):
                        loaded = load_moves(source)
                        rank_moves(loaded, self.body, 150, "push")
        for value in [0, -1, True, float("inf"), float("nan")]:
            with self.assertRaises(ValueError):
                rank_moves(self.moves, self.body, value, "push")
        with self.assertRaises(ValueError):
            rank_moves(self.moves, self.body, 150, "pull")
        with self.assertRaises(ValueError):
            self.decision(self.session("unknown"))

    def test_cli_errors_and_read_only_example(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "log.json"
            original = (DATA / "example_session_log.json").read_bytes()
            log.write_bytes(original)
            result = self.cli(log)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output["decision"]["move_id"], "knee-push-up")
            self.assertFalse(output["decision"]["flagged_jump"])
            self.assertEqual(log.read_bytes(), original)
            for text in ["[]", "{}", "broken json"]:
                log.write_text(text)
                result = self.cli(log)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
            log.write_bytes(original)
            self.assertEqual(self.cli(log, "--strength-reference", "0").returncode, 2)
            self.assertEqual(self.cli(log, "--pattern", "pull").returncode, 2)

    def test_cli_push_pattern_steps_and_surface_heights(self):
        # Failure inventory: gaps hidden by rounding, name/file ordering used
        # instead of torque, a strength reference changing the gaps, and height
        # labels attached to poses that cannot reach those surfaces.
        raw = list(reversed(json.loads((DATA / "moves.json").read_text())))
        for index, row in enumerate(raw):
            row["name"] = f"Reverse rank label {index:02d}"
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "log.json"
            log.write_text(json.dumps([{
                "date": "2026-10-19", "move_id": "wall-push-up", "reps": 8,
                "rpe": 7, "discomfort": False, "discomfort_notes": "",
            }]))
            catalogue = Path(folder) / "moves.json"
            catalogue.write_text(json.dumps(raw))
            evidence = []
            for reference in (150, 300):
                result = self.cli(log, "--moves", str(catalogue),
                                  "--strength-reference", str(reference))
                self.assertEqual(result.returncode, 0, result.stderr)
                ranking = json.loads(result.stdout)["ranking"]
                self.assertEqual([item["move_id"] for item in ranking], PUSH_STEPS)
                for left, right in zip(ranking, ranking[1:]):
                    jump = right["relative_torque"] / left["relative_torque"] - 1
                    with self.subTest(reference=reference, move=right["move_id"]):
                        self.assertGreaterEqual(jump, .10)
                        self.assertLessEqual(jump, .20)
                        self.assertLess(left["torque_nm"], right["torque_nm"])
                    evidence.append({"reference_nm": reference,
                                     "from": left["move_id"],
                                     "to": right["move_id"], "jump_fraction": jump})
            self.assertEqual(json.loads(catalogue.read_text()), raw)
        # Independently reconstruct wrist height above the foot pivot from the
        # stored segments and angles; heights apply only to the example body.
        for move_id, height in {
            "high-rail-push-up": 1.45, "rail-push-up": 1.25,
            "counter-tucked-push-up": .90, "counter-forward-push-up": .90,
            "incline-push-up": .75, "bench-push-up": .45, "step-push-up": .25,
        }.items():
            geometry = self.by_id[move_id].geometry
            theta = math.radians(geometry.body_angle_deg)
            alpha = math.radians(geometry.upper_arm_angle_deg)
            forearm = math.radians(geometry.upper_arm_angle_deg + geometry.elbow_angle_deg)
            span = sum(getattr(self.body, segment) for segment in geometry.support_segments)
            wrist_height = (span * math.sin(theta)
                            + self.body.upper_arm_m * math.sin(theta + alpha)
                            + self.body.forearm_m * math.sin(theta + forearm))
            with self.subTest(move=move_id):
                self.assertAlmostEqual(wrist_height, height, delta=.000001)
        print("PUSH_PATTERN_GAPS=" + json.dumps(evidence, sort_keys=True))

    def test_simulated_beginner_end_to_end(self):
        # Missed reps, excessive effort, every step, discomfort recovery, and
        # the ceiling; dates are a fictional software trace, not a schedule.
        scenarios = [
            ("wall-push-up", 5, 6, False, "hold", "wall-push-up", False),
            ("wall-push-up", 8, 8, False, "hold", "wall-push-up", False),
            ("wall-push-up", 8, 7, False, "progress", "high-rail-push-up", False),
            ("high-rail-push-up", 8, 7, False, "progress", "rail-push-up", False),
            ("rail-push-up", 8, 7, False, "progress", "counter-tucked-push-up", False),
            ("counter-tucked-push-up", 8, 7, False, "progress", "counter-forward-push-up", False),
            ("counter-forward-push-up", 12, 2, True, "regress", "counter-tucked-push-up", False),
            ("counter-tucked-push-up", 8, 6, False, "progress", "counter-forward-push-up", False),
            ("counter-forward-push-up", 8, 7, False, "progress", "incline-push-up", False),
            ("incline-push-up", 8, 7, False, "progress", "knee-push-up", False),
            ("knee-push-up", 8, 6, False, "progress", "bench-push-up", False),
            ("bench-push-up", 8, 7, False, "progress", "step-push-up", False),
            ("step-push-up", 8, 7, False, "progress", "full-push-up", False),
            ("full-push-up", 8, 7, False, "hold", "full-push-up", False),
        ]
        trace, history = [], []
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "beginner.json"
            for day, (move, reps, rpe, discomfort, action, target, flagged) in enumerate(
                    scenarios, start=1):
                history.append({
                    "date": f"2026-10-{day:02d}", "move_id": move,
                    "reps": reps, "rpe": rpe, "discomfort": discomfort,
                    "discomfort_notes": "Wrist discomfort" if discomfort else "",
                })
                log.write_text(json.dumps(history))
                result = self.cli(log)
                self.assertEqual(result.returncode, 0, result.stderr)
                decision = json.loads(result.stdout)["decision"]
                self.assertEqual(
                    (decision["action"], decision["move_id"], decision["flagged_jump"]),
                    (action, target, flagged))
                if action == "progress":
                    self.assertGreaterEqual(decision["jump_fraction"], .10)
                    self.assertLessEqual(decision["jump_fraction"], .20)
                trace.append({"session": history[-1], "decision": decision})
        print("BEGINNER_RUN=" + json.dumps(trace, sort_keys=True))

    def test_cli_band_boundaries_and_equal_distance_tie(self):
        # Failure inventory: floating-point endpoints fall outside the band;
        # a 10%/20% tie selects the larger step due to rounding noise.
        raw = json.loads((DATA / "moves.json").read_text())[-1]
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            log = folder / "log.json"
            log.write_text(json.dumps([{
                "date": "2026-10-19", "move_id": "base", "reps": 8,
                "rpe": 7, "discomfort": False, "discomfort_notes": "",
            }]))
            source = folder / "moves.json"
            for fractions, target in [
                ([.5, .55], "candidate-1"),
                ([.5, .6], "candidate-1"),
                ([.5, .55, .6], "candidate-1"),
            ]:
                variants = []
                for index, fraction in enumerate(fractions):
                    item = copy.deepcopy(raw)
                    item["id"] = "base" if index == 0 else f"candidate-{index}"
                    item["geometry"]["mass_fraction"] = fraction
                    variants.append(item)
                source.write_text(json.dumps(variants))
                result = self.cli(log, "--moves", str(source))
                self.assertEqual(result.returncode, 0, result.stderr)
                decision = json.loads(result.stdout)["decision"]
                self.assertEqual((decision["move_id"], decision["flagged_jump"]),
                                 (target, False))

    def test_cli_numeric_limits_fail_with_input_errors(self):
        # Failure inventory: huge JSON integers overflow float conversion;
        # finite inputs overflow derived force or progression ratios.
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            log = folder / "log.json"
            good_log = json.loads((DATA / "example_session_log.json").read_text())
            log.write_text(json.dumps(good_log))
            source = folder / "body.json"
            raw = json.loads((DATA / "example_body.json").read_text())
            for value in [10**400, 1e308]:
                source.write_text(json.dumps(dict(raw, mass_kg=value)))
                result = self.cli(log, "--body", str(source))
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
            bad_log = copy.deepcopy(good_log)
            bad_log[-1]["rpe"] = 10**400
            log.write_text(json.dumps(bad_log))
            result = self.cli(log)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            log.write_text(json.dumps([dict(good_log[0], reps=8, rpe=7)]))
            moves = json.loads((DATA / "moves.json").read_text())
            moves[0]["geometry"]["mass_fraction"] = 1e-309
            catalogue = folder / "moves.json"
            catalogue.write_text(json.dumps(moves))
            result = self.cli(log, "--moves", str(catalogue))
            self.assertEqual(result.returncode, 2)
            self.assertIn("error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
