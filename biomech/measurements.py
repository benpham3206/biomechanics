"""Manual/JSON body dimensions, in SI units; PLY is deliberately unsupported."""

from dataclasses import dataclass, fields

from .validation import from_mapping, positive, read_json


@dataclass(frozen=True)
class BodyDimensions:
    mass_kg: float
    torso_m: float
    thigh_m: float
    shank_m: float
    upper_arm_m: float
    forearm_m: float

    def __post_init__(self):
        for field in fields(self):
            positive(getattr(self, field.name), field.name)


def load_body(path):
    """Load exactly the BodyDimensions fields; invalid inputs raise ValueError."""
    return from_mapping(BodyDimensions, read_json(path))


def load_ply(path):
    """Future lidar-viewer PLY -> BodyDimensions adapter; never reads the file."""
    raise NotImplementedError(
        "PLY measurement extraction is not implemented. Use manual dimensions "
        "or load_body(JSON); point clouds need scale, landmarks, and mass input.")
