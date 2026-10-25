"""Mech-suit lever checks, written before biomech/suit.py.

Rules guarded: the trunk moment matches the hand calculation in
docs/mech-suit/SPEC.md; the spring is slack at and below its engage angle, so
it never pulls past upright; a design is rejected if its assist nears the
trunk's own gravity moment (recoil risk) or if the chest pad force passes the
interface limit; "feels like" kg follows from the moments; the assist-curve
script runs from the repo root.
"""

import math
from pathlib import Path
import subprocess
import sys
import unittest

from biomech.measurements import load_body
from biomech.suit import (SpringAssist, assist_torque, check_design, feels_like_kg,
                          interface_forces, load_case_poses, lumbar_compression, SIT_POSE,
                          trunk_moment)


ROOT = Path(__file__).resolve().parents[1]
FRAME = SpringAssist(stiffness_n_per_m=7200, cam_radius_m=0.08, engage_angle_deg=15,
                     limit_angle_deg=70)
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

    def test_spring_is_slack_at_and_below_engage_angle(self):
        for angle in (-10, 0, 10, 15):
            self.assertEqual(assist_torque(FRAME, angle).torque_nm, 0.0)
        at_60 = assist_torque(FRAME, 60)
        stretch = 0.08 * math.radians(45)
        self.assertAlmostEqual(at_60.force_n, 7200 * stretch, places=6)
        self.assertAlmostEqual(at_60.torque_nm, 7200 * stretch * 0.08, places=6)
        # Past the 70 deg limiter the torque plateaus at 7200 * 0.08^2 * 55 deg.
        self.assertAlmostEqual(assist_torque(FRAME, 110).torque_nm,
                               7200 * 0.08 ** 2 * math.radians(55), places=6)

    def test_safe_design_passes_and_unsafe_designs_fail(self):
        self.assertEqual(check_design(FRAME, self.body, POSES,
                                      chest_lever_m=0.44), [])
        strong = SpringAssist(stiffness_n_per_m=20000, cam_radius_m=0.08,
                              engage_angle_deg=15)
        issues = check_design(strong, self.body, POSES, chest_lever_m=0.44)
        self.assertTrue(any("gravity moment" in issue for issue in issues))
        self.assertTrue(any("chest" in issue for issue in issues))
        early = SpringAssist(stiffness_n_per_m=7200, cam_radius_m=0.08,
                             engage_angle_deg=0)
        self.assertTrue(any("engage" in issue for issue in check_design(
            early, self.body, POSES, chest_lever_m=0.44)))
        # Deep squat (hip 135 deg) without the stretch limiter: worst case fails.
        unlimited = SpringAssist(stiffness_n_per_m=7200, cam_radius_m=0.08,
                                 engage_angle_deg=15)
        self.assertEqual(check_design(unlimited, self.body, load_case_poses(110)[:110],
                                      chest_lever_m=0.44), [])
        self.assertNotEqual(check_design(unlimited, self.body, POSES,
                                         chest_lever_m=0.44), [])
        self.assertAlmostEqual(assist_torque(FRAME, 135).torque_nm,
                               assist_torque(FRAME, 70).torque_nm)
        # Known-bad case: sitting with the clutch on pushes the trunk backward.
        self.assertTrue(any("gravity moment" in issue for issue in check_design(
            FRAME, self.body, [SIT_POSE], chest_lever_m=0.44)))
        # Same torque through a soft band (lever = band radius) overloads the strap.
        self.assertTrue(any("chest" in issue for issue in check_design(
            FRAME, self.body, POSES, chest_lever_m=0.15)))

    def test_interface_forces_are_torque_over_lever(self):
        chest, thigh = interface_forces(60, chest_lever_m=0.44, thigh_lever_m=0.30)
        self.assertAlmostEqual(chest, 60 / 0.44)
        self.assertAlmostEqual(thigh, 60 / 0.30)

    def test_feels_like(self):
        tau = assist_torque(FRAME, 90).torque_nm
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
            SpringAssist(stiffness_n_per_m=0, cam_radius_m=0.08, engage_angle_deg=15)
        with self.assertRaises(ValueError):
            SpringAssist(stiffness_n_per_m=1, cam_radius_m=0.08, engage_angle_deg=15,
                         limit_angle_deg=10)
        with self.assertRaises(ValueError):
            trunk_moment(self.body, 200)
        with self.assertRaises(ValueError):
            trunk_moment(self.body, 90, -1)

    def test_assist_curve_script(self):
        run = subprocess.run([sys.executable, "scripts/assist_curve.py"], cwd=ROOT,
                             text=True, capture_output=True, timeout=10, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("safety check: pass", run.stdout)
        self.assertIn("feels like", run.stdout)


if __name__ == "__main__":
    unittest.main()
