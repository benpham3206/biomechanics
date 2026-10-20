"""A single planar movement lever, torque ranking, and progression policy."""

from dataclasses import dataclass
import math

from .validation import from_mapping, number, positive, read_json, text


@dataclass(frozen=True)
class Geometry:
    support_segments: list
    mass_fraction: float
    com_fraction: float
    body_angle_deg: float
    upper_arm_angle_deg: float
    elbow_angle_deg: float

    def __post_init__(self):
        allowed = {"torso_m", "thigh_m", "shank_m"}
        if (not isinstance(self.support_segments, list) or not self.support_segments
                or any(segment not in allowed for segment in self.support_segments)
                or len(set(self.support_segments)) != len(self.support_segments)):
            raise ValueError("support_segments must be unique torso/thigh/shank field names")
        for name in ("mass_fraction", "com_fraction"):
            number(getattr(self, name), name, minimum=0, maximum=1)
            positive(getattr(self, name), name)
        number(self.body_angle_deg, "body_angle_deg", minimum=0, maximum=90)
        if self.body_angle_deg == 90:
            raise ValueError("body_angle_deg must be less than 90")
        for name in ("upper_arm_angle_deg", "elbow_angle_deg"):
            number(getattr(self, name), name, minimum=-180, maximum=180)


@dataclass(frozen=True)
class Move:
    id: str
    name: str
    pattern: str
    muscle_groups: list
    geometry: Geometry
    rep_target: int

    def __post_init__(self):
        for name in ("id", "name", "pattern"):
            text(getattr(self, name), name)
        if not isinstance(self.muscle_groups, list) or not self.muscle_groups:
            raise ValueError("muscle_groups must be a nonempty array")
        for group in self.muscle_groups:
            text(group, "muscle group")
        if not isinstance(self.geometry, Geometry):
            raise ValueError("geometry must be Geometry")
        if type(self.rep_target) is not int or self.rep_target <= 0:
            raise ValueError("rep_target must be a positive integer")


@dataclass(frozen=True)
class LeverLoad:
    hand_force_n: float
    moment_arm_m: float
    torque_nm: float


@dataclass(frozen=True)
class RankedMove:
    move: Move
    load: LeverLoad
    relative_torque: float


@dataclass(frozen=True)
class Decision:
    action: str
    move_id: str | None
    reason: str
    jump_fraction: float | None = None
    flagged_jump: bool = False


def load_moves(path):
    raw = read_json(path)
    if not isinstance(raw, list) or not raw:
        raise ValueError("Move catalogue must be a nonempty array")
    moves = []
    for index, row in enumerate(raw):
        if not isinstance(row, dict):
            raise ValueError(f"Move row {index + 1} must be an object")
        item = dict(row)
        item["geometry"] = from_mapping(Geometry, item.get("geometry"))
        moves.append(from_mapping(Move, item))
    if len({move.id for move in moves}) != len(moves):
        raise ValueError("Move IDs must be unique")
    return moves


def lever_load(move, body):
    """Total transverse hand force and bilateral external shoulder torque (SI)."""
    geometry = move.geometry
    alpha = math.radians(geometry.upper_arm_angle_deg)
    beta = math.radians(geometry.elbow_angle_deg)
    arm = body.upper_arm_m * math.cos(alpha) + body.forearm_m * math.cos(alpha + beta)
    positive(arm, "headward shoulder-to-hand projection")
    span = sum(getattr(body, segment) for segment in geometry.support_segments)
    weight = body.mass_kg * geometry.mass_fraction * 9.81
    hand_force = (weight * geometry.com_fraction * span
                  * math.cos(math.radians(geometry.body_angle_deg)) / (span + arm))
    torque = hand_force * arm
    positive(hand_force, "computed hand force")
    positive(torque, "computed torque")
    return LeverLoad(hand_force, arm, torque)


def rank_moves(moves, body, strength_reference_nm, pattern):
    """Rank a pattern by torque / a positive bilateral strength reference."""
    positive(strength_reference_nm, "strength_reference_nm")
    if len({move.id for move in moves}) != len(moves):
        raise ValueError("Move IDs must be unique")
    ranked = []
    for move in moves:
        if move.pattern == pattern:
            load = lever_load(move, body)
            relative = load.torque_nm / strength_reference_nm
            positive(relative, "computed relative torque")
            ranked.append(RankedMove(move, load, relative))
    if not ranked:
        raise ValueError(f"No moves in pattern: {pattern}")
    return sorted(ranked, key=lambda item: (item.relative_torque, item.move.id))


def recommend(session, moves, body, strength_reference_nm):
    """Return a suggestion only; never change a log or a strength reference."""
    current_move = next((move for move in moves if move.id == session.move_id), None)
    if current_move is None:
        raise ValueError(f"Unknown move_id: {session.move_id}")
    ranked = rank_moves(moves, body, strength_reference_nm, current_move.pattern)
    current = next(item for item in ranked if item.move.id == session.move_id)
    if session.discomfort:
        easier = [item for item in ranked if item.relative_torque < current.relative_torque]
        target = easier[-1].move.id if easier else None
        reason = ("Discomfort reported: stop this move. "
                  + ("An easier option is listed for after discomfort resolves."
                     if target else "No easier move exists in this pattern; stop here."))
        return Decision("regress", target, reason)
    if session.reps < current_move.rep_target:
        return Decision("hold", current_move.id,
                        f"Below rep target: {session.reps}/{current_move.rep_target}.")
    if session.rpe > 7:
        return Decision("hold", current_move.id, f"RPE {session.rpe:g} exceeds 7.")
    harder = [item for item in ranked if item.relative_torque > current.relative_torque]
    if not harder:
        return Decision("hold", current_move.id, "Already at the top of this pattern.")
    candidates = [(item, item.relative_torque / current.relative_torque - 1)
                  for item in harder]
    for _, jump in candidates:
        positive(jump, "computed progression jump")
    in_band = [(item, jump) for item, jump in candidates
               if .10 <= jump <= .20 or math.isclose(jump, .10) or math.isclose(jump, .20)]
    target, jump = min(in_band or candidates,
                       key=lambda pair: (abs(pair[1] - .15), pair[0].relative_torque))
    flagged = not in_band
    reason = (f"Rep target met at RPE <= 7 without discomfort; "
              f"relative torque increases {jump:.1%}. "
              + ("Closest available step is outside the 10-20% band; review the jump."
                 if flagged else "Step is within the 10-20% band."))
    return Decision("progress", target.move.id, reason, jump, flagged)
