"""Print the v0 hip-spring assist curve, load cases, and safety check.

Example data only: data/example_body.json is fictional and the spring is the
spec's sizing guess, not a measured part. Usage: python3 scripts/assist_curve.py
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from biomech.measurements import load_body  # noqa: E402
from biomech.suit import (CHEST_LIMIT_N, SpringAssist, assist_torque,  # noqa: E402
                          check_design, feels_like_kg, interface_forces,
                          load_case_poses, lumbar_compression, trunk_moment,
                          SIT_POSE)

CHEST_LEVER_M, THIGH_LEVER_M, LOAD_KG = 0.44, 0.30, 15
SQUAT_REACH_M = 0.60  # box centre ahead of the hip in a squat lift (example)


def row(body, spring, label, hip, trunk, reach=None):
    total = trunk_moment(body, trunk, LOAD_KG, reach)
    tau = assist_torque(spring, hip).torque_nm
    chest, thigh = interface_forces(tau, CHEST_LEVER_M, THIGH_LEVER_M)
    felt = feels_like_kg(body, trunk, LOAD_KG, tau, reach) if trunk else LOAD_KG
    before = lumbar_compression(body, trunk, LOAD_KG, reach)
    after = lumbar_compression(body, trunk, LOAD_KG, reach, assist_nm=tau)
    print(f"{label:13} | {hip:3d}/{trunk:3d} | {trunk_moment(body, trunk):9.1f} | "
          f"{total:8.1f} | {tau:6.1f} | {chest:5.0f} | {thigh:5.0f} | {felt:6.1f} | "
          f"{before:5.0f} -> {after:5.0f}")


def main():
    body = load_body(ROOT / "data" / "example_body.json")
    spring = SpringAssist(stiffness_n_per_m=7200, cam_radius_m=0.08,
                          engage_angle_deg=15, limit_angle_deg=70)
    print(f"Example body {body.mass_kg} kg (fictional). Spring 7200 N/m on a 0.08 m "
          f"cam, slack below 15 deg, stretch limiter at 70 deg. Box {LOAD_KG} kg.")
    print("pose          | hip/trunk | own trunk | with box | assist | chest | thigh "
          "| box feels like kg | L5/S1 N unaided -> suit")
    print("              |    deg    |    Nm     |    Nm    |   Nm   |   N   |   N   |")
    for angle in (0, 15, 30, 45, 60, 75, 90, 110):
        row(body, spring, "stoop", angle, angle)
    row(body, spring, "squat lift", 135, 45, SQUAT_REACH_M)
    sit = check_design(spring, body, [SIT_POSE], CHEST_LEVER_M)
    print("sitting, clutch ON: " + ("FLAGGED, so the clutch must be OFF to sit"
                                     if sit else "not flagged (check is broken)"))
    issues = [] if sit else ["sitting check did not flag the known-bad pose"]
    issues += check_design(spring, body, load_case_poses(110), CHEST_LEVER_M)
    print(f"chest limit {CHEST_LIMIT_N:.0f} N; safety check: "
          + ("pass" if not issues else "FAIL\n  " + "\n  ".join(issues)))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
