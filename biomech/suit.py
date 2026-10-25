"""Mech-suit v0: trunk lever about the hip, a hip gas strut, and its limits.

One planar lever: head, arms and trunk (HAT) pivot about a lumped hip/L5-S1
point. Trunk angle is forward lean from vertical; gravity acts on it. Hip angle
is trunk-to-thigh flexion; the strut sees it. In a stoop they are equal; in a
squat, hip = trunk + thigh angle. Static only. See docs/mech-suit/SPEC.md.
"""

from dataclasses import dataclass
import math

from .validation import number, positive

G = 9.81
HAT_MASS_FRACTION = 0.678   # Winter, Biomechanics and Motor Control, Table 4.1
HAT_COM_FRACTION = 0.626    # of greater-trochanter-to-shoulder length, same table
EXTENSOR_ARM_M = 0.05       # common single-muscle simplification (McGill & Norman 1987)
CHEST_LIMIT_N = 185.0       # male chest-strap discomfort 230 +/- 45 N, mean - 1 SD
                            # (Kozinc et al. 2021, Applied Ergonomics 103379)
RECOIL_CAP = 0.6            # assist must stay below 60% of the trunk's own moment


def _angle(angle_deg, name="trunk_angle_deg"):
    number(angle_deg, name, minimum=-30, maximum=150)


def trunk_moment(body, trunk_angle_deg, load_kg=0.0, load_reach_m=None):
    """External extensor moment at the hip/low back (Nm) to hold this pose.

    The load hangs from the hands; default reach is the shoulder's horizontal
    distance, torso_m * sin(angle). Pass load_reach_m for a squat lift.
    """
    _angle(trunk_angle_deg)
    number(load_kg, "load_kg", minimum=0)
    s = math.sin(math.radians(trunk_angle_deg))
    hat = body.mass_kg * HAT_MASS_FRACTION * G * HAT_COM_FRACTION * body.torso_m * s
    if load_reach_m is None:
        reach = body.torso_m * s
    else:
        number(load_reach_m, "load_reach_m", minimum=0)
        reach = load_reach_m
    return hat + load_kg * G * reach


@dataclass(frozen=True)
class StrutAssist:
    """One gas strut per side, pushing between the trunk strut and a hip crank.

    Geometry (per side): the strut's top end sits trunk_arm_m from the hip
    along the trunk strut; its bottom end sits crank_m from the hip on a crank
    fixed to the thigh bar. Standing, the angle between them is crank_angle_deg;
    hip flexion h closes it to crank_angle_deg - h, which shortens the strut.
    A slot at one end (lost motion) leaves the strut idle until its
    centre-to-centre length falls to extended_m; it must never bottom out at
    compressed_m inside the range of motion. Force rises linearly by
    progression (fraction) over the stroke; 0.3 is an assumption until the
    bench test measures it. Same idea as the gas-spring Laevo and BackX.
    """
    force_n: float
    trunk_arm_m: float
    crank_m: float
    crank_angle_deg: float
    extended_m: float
    compressed_m: float
    progression: float = 0.3
    sides: int = 2

    def __post_init__(self):
        for name in ("force_n", "trunk_arm_m", "crank_m", "extended_m", "compressed_m"):
            positive(getattr(self, name), name)
        number(self.crank_angle_deg, "crank_angle_deg", minimum=1, maximum=179)
        number(self.progression, "progression", minimum=0, maximum=2)
        if self.compressed_m >= self.extended_m:
            raise ValueError("compressed_m must be shorter than extended_m")
        if type(self.sides) is not int or self.sides not in (1, 2):
            raise ValueError("sides must be 1 or 2")

    def length_m(self, hip_angle_deg):
        phi = math.radians(self.crank_angle_deg - hip_angle_deg)
        a, b = self.trunk_arm_m, self.crank_m
        return math.sqrt(a * a + b * b - 2 * a * b * math.cos(phi))

    def engage_angle_deg(self):
        """Hip angle where the slot closes and the strut starts pushing."""
        a, b, ext = self.trunk_arm_m, self.crank_m, self.extended_m
        c = (a * a + b * b - ext * ext) / (2 * a * b)
        if c <= -1:
            return 0.0  # strut is already loaded when standing
        if c >= 1:
            raise ValueError("strut never engages with this geometry")
        return self.crank_angle_deg - math.degrees(math.acos(c))


@dataclass(frozen=True)
class Assist:
    force_n: float      # strut force, per side
    torque_nm: float    # total hip extension torque, all sides


def assist_torque(strut, hip_angle_deg):
    _angle(hip_angle_deg, "hip_angle_deg")
    length = strut.length_m(hip_angle_deg)
    if length >= strut.extended_m or hip_angle_deg >= strut.crank_angle_deg:
        return Assist(0.0, 0.0)
    stroke = strut.extended_m - strut.compressed_m
    force = strut.force_n * (1 + strut.progression
                             * min(1.0, (strut.extended_m - length) / stroke))
    phi = math.radians(strut.crank_angle_deg - hip_angle_deg)
    arm = strut.trunk_arm_m * strut.crank_m * math.sin(phi) / length
    return Assist(force, strut.sides * force * arm)


def interface_forces(torque_nm, chest_lever_m, thigh_lever_m):
    """Pad forces (N) that react the assist torque: torque / lever length."""
    positive(chest_lever_m, "chest_lever_m")
    positive(thigh_lever_m, "thigh_lever_m")
    return torque_nm / chest_lever_m, torque_nm / thigh_lever_m


def feels_like_kg(body, trunk_angle_deg, load_kg, assist_nm, load_reach_m=None):
    """Load that needs the same back moment unaided. Never below zero."""
    reach = (body.torso_m * math.sin(math.radians(trunk_angle_deg))
             if load_reach_m is None else load_reach_m)
    positive(reach, "load reach")
    return max(0.0, load_kg - assist_nm / (G * reach))


def lumbar_compression(body, trunk_angle_deg, load_kg=0.0, load_reach_m=None,
                       assist_nm=0.0, added_axial_n=0.0):
    """Rough L5/S1 compression (N): extensor force + weight along the spine.

    added_axial_n is any suit force pressing along the spine (a soft band's
    tension); a rigid frame reacting at chest and thigh pads adds about none.
    """
    moment = max(0.0, trunk_moment(body, trunk_angle_deg, load_kg, load_reach_m)
                 - assist_nm)
    axial = ((body.mass_kg * HAT_MASS_FRACTION + load_kg) * G
             * math.cos(math.radians(trunk_angle_deg)))
    return moment / EXTENSOR_ARM_M + axial + added_axial_n


# v0 build (docs/mech-suit/BUILD.md): one 400 N, 12 in gas strut per side.
V0_STRUT = StrutAssist(force_n=400, trunk_arm_m=0.27, crank_m=0.06,
                       crank_angle_deg=150, extended_m=0.305, compressed_m=0.206)

SIT_POSE = (90, 5)  # hip 90, trunk 5 deg: sitting in a chair


def load_case_poses(max_stoop_deg=110):
    """(hip_deg, trunk_deg) poses with the clutch ON: every stoop angle, and
    squat lifts with thighs horizontal (hip = trunk + 90) for trunk 30..45 deg,
    which reach the deepest hip flexion (135 deg).

    Sitting or an upright deep squat (hip ~90+, trunk near 0) is NOT here: any
    hip assist then pushes the trunk backward, so the clutch must be OFF.
    SIT_POSE is kept as the known-bad case that check_design must flag.
    """
    stoop = [(a, a) for a in range(1, int(max_stoop_deg) + 1)]
    squat = [(t + 90, t) for t in range(30, 46)]
    return stoop + squat


def check_design(strut, body, poses, chest_lever_m, max_hip_deg=135,
                 chest_limit_n=CHEST_LIMIT_N, recoil_cap=RECOIL_CAP):
    """Return safety issues over (hip_deg, trunk_deg) poses; empty means pass."""
    issues = []
    if strut.engage_angle_deg() < 5:
        issues.append("strut must engage at >= 5 degrees so it is slack when upright")
    if strut.length_m(max_hip_deg) <= strut.compressed_m:
        issues.append(f"strut bottoms out before {max_hip_deg} deg hip flexion, "
                      "which would block motion")
    for hip, trunk in poses:
        tau = assist_torque(strut, hip).torque_nm
        own = trunk_moment(body, trunk)
        if tau > recoil_cap * own:
            issues.append(f"assist {tau:.1f} Nm exceeds {recoil_cap:.0%} of the "
                          f"trunk's own gravity moment {own:.1f} Nm at hip {hip} / "
                          f"trunk {trunk} deg")
            break
    for hip, _ in poses:
        chest = assist_torque(strut, hip).torque_nm / chest_lever_m
        if chest > chest_limit_n:
            issues.append(f"chest pad force {chest:.0f} N exceeds {chest_limit_n:.0f} N "
                          f"at hip {hip} deg")
            break
    return issues
