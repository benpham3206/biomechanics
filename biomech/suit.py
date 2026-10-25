"""Mech-suit v0: trunk lever about the hip, a hip spring, and its limits.

One planar lever: head, arms and trunk (HAT) pivot about a lumped hip/L5-S1
point. Trunk angle is forward lean from vertical; gravity acts on it. Hip angle
is trunk-to-thigh flexion; the spring sees it. In a stoop they are equal; in a
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
class SpringAssist:
    """A linear spring wound on a hip cam: slack until engage_angle_deg.

    limit_angle_deg is a stretch limiter (a strap beside the spring): past it
    the spring stops stretching, so torque plateaus instead of growing.
    """
    stiffness_n_per_m: float
    cam_radius_m: float
    engage_angle_deg: float
    limit_angle_deg: float | None = None

    def __post_init__(self):
        positive(self.stiffness_n_per_m, "stiffness_n_per_m")
        positive(self.cam_radius_m, "cam_radius_m")
        _angle(self.engage_angle_deg, "engage_angle_deg")
        if self.limit_angle_deg is not None:
            _angle(self.limit_angle_deg, "limit_angle_deg")
            if self.limit_angle_deg <= self.engage_angle_deg:
                raise ValueError("limit_angle_deg must exceed engage_angle_deg")


@dataclass(frozen=True)
class Assist:
    force_n: float
    torque_nm: float


def assist_torque(spring, hip_angle_deg):
    _angle(hip_angle_deg, "hip_angle_deg")
    angle = hip_angle_deg
    if spring.limit_angle_deg is not None:
        angle = min(angle, spring.limit_angle_deg)
    stretch = spring.cam_radius_m * math.radians(
        max(0.0, angle - spring.engage_angle_deg))
    force = spring.stiffness_n_per_m * stretch
    return Assist(force, force * spring.cam_radius_m)


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


SIT_POSE = (90, 5)  # hip 90, trunk 5 deg: sitting in a chair


def load_case_poses(max_stoop_deg=110):
    """(hip_deg, trunk_deg) poses with the clutch ON: every stoop angle, and
    squat lifts with thighs horizontal (hip = trunk + 90) for trunk 30..45 deg.

    Sitting or an upright deep squat (hip ~90+, trunk near 0) is NOT here: any
    hip spring then pushes the trunk backward, so the clutch must be OFF.
    SIT_POSE is kept as the known-bad case that check_design must flag.
    """
    stoop = [(a, a) for a in range(1, int(max_stoop_deg) + 1)]
    squat = [(t + 90, t) for t in range(30, 46)]
    return stoop + squat


def check_design(spring, body, poses, chest_lever_m,
                 chest_limit_n=CHEST_LIMIT_N, recoil_cap=RECOIL_CAP):
    """Return safety issues over (hip_deg, trunk_deg) poses; empty means pass."""
    issues = []
    if spring.engage_angle_deg < 5:
        issues.append("spring must engage at >= 5 degrees so it is slack when upright")
    for hip, trunk in poses:
        tau = assist_torque(spring, hip).torque_nm
        own = trunk_moment(body, trunk)
        if tau > recoil_cap * own:
            issues.append(f"assist {tau:.1f} Nm exceeds {recoil_cap:.0%} of the "
                          f"trunk's own gravity moment {own:.1f} Nm at hip {hip} / "
                          f"trunk {trunk} deg")
            break
    for hip, _ in poses:
        chest = assist_torque(spring, hip).torque_nm / chest_lever_m
        if chest > chest_limit_n:
            issues.append(f"chest pad force {chest:.0f} N exceeds {chest_limit_n:.0f} N "
                          f"at hip {hip} deg")
            break
    return issues
