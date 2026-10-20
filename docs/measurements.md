# Body-measurement interface

The shared boundary is `BodyDimensions`, a frozen Python dataclass in
`biomech.measurements`. All values must be finite, positive numbers. Boolean
values and numeric strings are rejected. Use kg and metres, not pounds or cm.

| Field | Manual input definition |
| --- | --- |
| `mass_kg` | Whole body mass from a scale |
| `torso_m` | Shoulder-to-hip segment length |
| `thigh_m` | Hip-to-knee segment length |
| `shank_m` | Knee-to-ankle segment length |
| `upper_arm_m` | Shoulder-to-elbow segment length |
| `forearm_m` | Elbow-to-wrist segment length |

Use approximate joint centres and straight segment distances. Use one consistent
side; v1 assumes equal sides. These rough manual inputs do not produce a
clinical measurement. Hands, feet, head, and segment-specific masses are not
separate fields. See the model for how the effective span and COM are estimated.

## Implemented sources

Manual Python source:

```python
from biomech.measurements import BodyDimensions

body = BodyDimensions(
    mass_kg=70, torso_m=0.55, thigh_m=0.45, shank_m=0.45,
    upper_arm_m=0.30, forearm_m=0.25,
)
```

JSON source:

```python
from biomech.measurements import load_body

body = load_body("data/example_body.json")
```

The JSON object has exactly the six fields above, with no missing or unknown
fields. [The example](../data/example_body.json) is fictional. `load_body`
returns `BodyDimensions`. Invalid data raises `ValueError`; file errors raise
`OSError`. V1 checks values and units by contract, not by guessing whether a
number is a plausible human dimension.

The strength reference is a separate argument to ranking and progression. It
is not a body dimension. It must be positive, finite, and in bilateral Nm.

## Planned PLY source: unimplemented

`load_ply(path) -> BodyDimensions` is the reserved adapter for a PLY export from
Ben's **lidar-viewer** repo, using an iPhone LiDAR point cloud. Calling it always
raises `NotImplementedError`, even if the file exists. It does not open or parse
the file and does not invoke any external program.

A future implementation must establish coordinate units and scale, separate
the person from the scene, identify joint landmarks, report uncertainty, and
obtain mass from a separate manual source. The adapter should return the same
validated `BodyDimensions` object. The actual lidar-viewer export schema has
not been inspected in v1. No assumption about its PLY properties is encoded.
