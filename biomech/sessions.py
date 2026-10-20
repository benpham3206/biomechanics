"""One completed set per session row; caller owns storage and logging."""

from dataclasses import dataclass
from datetime import date

from .validation import from_mapping, number, read_json, text


@dataclass(frozen=True)
class Session:
    date: str
    move_id: str
    reps: int
    rpe: float
    discomfort: bool
    discomfort_notes: str

    def __post_init__(self):
        if (not isinstance(self.date, str)
                or date.fromisoformat(self.date).isoformat() != self.date):
            raise ValueError("date must be an actual date in YYYY-MM-DD format")
        text(self.move_id, "move_id")
        if type(self.reps) is not int or self.reps < 0:
            raise ValueError("reps must be a nonnegative integer")
        number(self.rpe, "rpe", minimum=1, maximum=10)
        if type(self.discomfort) is not bool:
            raise ValueError("discomfort must be true or false")
        if not isinstance(self.discomfort_notes, str):
            raise ValueError("discomfort_notes must be a string")
        if self.discomfort and not self.discomfort_notes.strip():
            raise ValueError("discomfort_notes is required when discomfort is true")


def load_sessions(path, moves):
    """Validate a chronological JSON array against the supplied move catalogue."""
    raw = read_json(path)
    if not isinstance(raw, list):
        raise ValueError("Session log must be an array")
    known_ids = {move.id for move in moves}
    sessions = []
    for index, row in enumerate(raw):
        try:
            session = from_mapping(Session, row)
            if session.move_id not in known_ids:
                raise ValueError(f"Unknown move_id: {session.move_id}")
            if sessions and session.date < sessions[-1].date:
                raise ValueError("Session dates must be in chronological order")
        except ValueError as exc:
            raise ValueError(f"Session row {index + 1}: {exc}") from exc
        sessions.append(session)
    return sessions
