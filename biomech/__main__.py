"""Read-only JSON command-line interface."""

import argparse
from dataclasses import asdict
import json

from .core import load_moves, rank_moves, recommend
from .measurements import load_body
from .sessions import load_sessions


def main():
    parser = argparse.ArgumentParser(description="Rank push moves and suggest a next step.")
    parser.add_argument("--body", required=True, help="BodyDimensions JSON path")
    parser.add_argument("--moves", required=True, help="Move catalogue JSON path")
    parser.add_argument("--log", required=True, help="Chronological session-log JSON path")
    parser.add_argument("--strength-reference", type=float, required=True,
                        help="Positive bilateral shoulder strength reference in Nm")
    parser.add_argument("--pattern", default="push")
    args = parser.parse_args()
    try:
        body = load_body(args.body)
        moves = load_moves(args.moves)
        sessions = load_sessions(args.log, moves)
        ranked = rank_moves(moves, body, args.strength_reference, args.pattern)
        ids = {item.move.id for item in ranked}
        latest = next((session for session in reversed(sessions) if session.move_id in ids), None)
        if latest is None:
            raise ValueError(f"No session for pattern: {args.pattern}; log a completed set first")
        decision = recommend(latest, moves, body, args.strength_reference)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    output = {
        "pattern": args.pattern,
        "ranking": [{"move_id": item.move.id, "name": item.move.name,
                     "rep_target": item.move.rep_target,
                     **asdict(item.load), "relative_torque": item.relative_torque}
                    for item in ranked],
        "latest_session": asdict(latest),
        "decision": asdict(decision),
    }
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
