"""Shared checks for JSON and direct Python inputs."""

import json
from pathlib import Path
import sys


def number(value, name, *, minimum, maximum=sys.float_info.max):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not minimum <= value <= maximum):
        raise ValueError(f"{name} must be a finite number in [{minimum}, {maximum}]")


def positive(value, name):
    number(value, name, minimum=0)
    if value == 0:
        raise ValueError(f"{name} must be greater than zero")


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def from_mapping(cls, value):
    if not isinstance(value, dict):
        raise ValueError(f"{cls.__name__} must be an object")
    try:
        return cls(**value)
    except TypeError as exc:
        raise ValueError(f"Invalid {cls.__name__} fields: {exc}") from exc


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
