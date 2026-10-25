"""Mech-suit lever checks (docs/mech-suit/SPEC.md, BUILD.md).

Rules guarded: the trunk moment matches the hand calculation; the strut is
idle until its slot closes, so it never pushes when standing; torque follows
the strut geometry; a design is rejected if its assist nears the trunk's own
gravity moment (recoil risk), if the chest pad force passes the interface
limit, or if the strut bottoms out inside the range of motion (it would block
movement); sitting with the clutch on stays a known-bad case; "feels like"
kg follows from the moments; the assist-curve script runs from the repo root.
"""

from dataclasses import replace
import math
from pathlib import Path
import subprocess
import sys
import unittest

from biomech.measurements import load_body
from biomech.suit import (SIT_POSE, V0_STRUT, StrutAssist, assist_torque, check_design,
                          feels_like_kg, interface_forces, load_case_poses,
                          lumbar_compression, trunk_moment)


ROOT = Path(__file__).resolve().parents[1]
POSES = load_case_poses(110)


class SuitLever(unittest.TestCase):
    def setUp(self):
        self.body = load_body(ROOT / "data" / "example_body.json")

    def test_trunk_moment_hand_calculation(self):
        # 0.678 * 70 kg * 9.81 * (0.626 * 0.55 m) = 160.29 Nm at 90 degrees.
        self.assertAlmostEqual(trunk_moment(self.body, 90), 160.29, places=1)
        self.assertAlmostEqual(trunk_moment(self.body, 0), 0.0, places=9)
        # Stoop, 10 kg held under the shoulders: + 10 * 9.81 * 0.55 m.
        self.assertAlmostEqual(trunk_moment(self.body, 90, 10), 214.25, places=1)
        # Squat lift: trunk 45 degrees, 10 kg at an explicit 0.60 m reach.
        self.assertAlmostEqual(trunk_moment(self.body, 45, 10, 0.60), 172.20, places=1)

    def test_strut_is_idle_until_the_slot_closes(self):
        engage = V0_STRUT.engage_angle_deg()
        self.assertAlmostEqual(engage, 29.33, places=1)
        for angle in (-10, 0, 15, 29):
            self.assertEqual(assist_torque(V0_STRUT, angle).torque_nm, 0.0)
        self.assertGreater(assist_torque(V0_STRUT, 30).torque_nm, 0.0)

    def test_strut_torque_hand_calculation(self):
        # Hip 90: phi = 60 deg, L = sqrt(.27^2 + .06^2 - 2*.27*.06*cos 60).
        length = math.sqrt(0.27 ** 2 + 0.06 ** 2 - 2 * 0.27 * 0.06 * 0.5)
        force = 400 * (1 + 0.3 * (0.305 - length) / (0.305 - 0.206))
        arm = 0.27 * 0.06 * math.sin(math.radians(60)) / length
        result = assist_torque(V0_STRUT, 90)
        self.assertAlmostEqual(result.force_n, force, places=6)
        self.assertAlmostEqual(result.torque_nm, 2 * force * arm, places=6)

    def test_v0_passes_and_unsafe_designs_fail(self):
        self.assertEqual(check_design(V0_STRUT, self.body, POSES, chest_lever_m=0.44), [])
        strong = replace(V0_STRUT, force_n=800)
        issues = check_design(strong, self.body, POSES, chest_lever_m=0.44)
        self.assertTrue(any("gravity moment" in issue for issue in issues))
        self.assertTrue(any("chest" in issue for issue in issues))
        preloaded = replace(V0_STRUT, extended_m=0.33)
        self.assertTrue(any("engage" in issue for issue in check_design(
            preloaded, self.body, POSES, chest_lever_m=0.44)))
        short = replace(V0_STRUT, compressed_m=0.215)
        self.assertTrue(any("bottoms out" in issue for issue in check_design(
            short, self.body, POSES, chest_lever_m=0.44)))
        # Known-bad case: sitting with the clutch on pushes the trunk backward.
        self.assertTrue(any("gravity moment" in issue for issue in check_design(
            V0_STRUT, self.body, [SIT_POSE], chest_lever_m=0.44)))
        # Same torque through a soft band (lever = band radius) overloads the strap.
        self.assertTrue(any("chest" in issue for issue in check_design(
            V0_STRUT, self.body, POSES, chest_lever_m=0.15)))

    def test_interface_forces_are_torque_over_lever(self):
        chest, thigh = interface_forces(60, chest_lever_m=0.44, thigh_lever_m=0.30)
        self.assertAlmostEqual(chest, 60 / 0.44)
        self.assertAlmostEqual(thigh, 60 / 0.30)

    def test_feels_like(self):
        tau = assist_torque(V0_STRUT, 90).torque_nm
        felt = feels_like_kg(self.body, 90, 15, tau)
        self.assertAlmostEqual(felt, 15 - tau / (9.81 * 0.55), places=6)
        self.assertEqual(feels_like_kg(self.body, 90, 2, 500), 0.0)

    def test_compression_drops_by_saved_muscle_force(self):
        no_suit = lumbar_compression(self.body, 90, 10)
        self.assertAlmostEqual(no_suit, 214.25 / 0.05, delta=2)
        suit = lumbar_compression(self.body, 90, 10, assist_nm=60)
        self.assertAlmostEqual(no_suit - suit, 60 / 0.05, places=6)
        band = lumbar_compression(self.body, 90, 10, assist_nm=60, added_axial_n=400)
        self.assertAlmostEqual(band - suit, 400, places=6)

    def test_rejects_bad_inputs(self):
        with self.assertRaises(ValueError):
            replace(V0_STRUT, force_n=0)
        with self.assertRaises(ValueError):
            replace(V0_STRUT, compressed_m=0.4)
        with self.assertRaises(ValueError):
            trunk_moment(self.body, 200)
        with self.assertRaises(ValueError):
            trunk_moment(self.body, 90, -1)
        self.assertIsInstance(V0_STRUT, StrutAssist)

    def test_assist_curve_script(self):
        run = subprocess.run([sys.executable, "scripts/assist_curve.py"], cwd=ROOT,
                             text=True, capture_output=True, timeout=10, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("safety check: pass", run.stdout)
        self.assertIn("feels like", run.stdout)


if __name__ == "__main__":
    unittest.main()
