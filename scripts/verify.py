"""Run all checks and retain a repeatable JSON evidence artifact."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    transcript = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    with contextlib.redirect_stdout(transcript), contextlib.redirect_stderr(transcript):
        result = unittest.TextTestRunner(stream=transcript, verbosity=2).run(suite)
    demo = subprocess.run(
        [sys.executable, "-m", "biomech", "--body", "data/example_body.json",
         "--moves", "data/moves.json", "--log", "data/example_session_log.json",
         "--strength-reference", "150"],
        cwd=ROOT, text=True, capture_output=True, timeout=10, check=False)
    passed = result.wasSuccessful() and result.testsRun > 0 and demo.returncode == 0
    report = {
        "passed": passed, "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "test_transcript": transcript.getvalue(),
        "example_exit_code": demo.returncode,
        "example_stdout": demo.stdout, "example_stderr": demo.stderr,
    }
    artifact = ROOT / "artifacts" / "verification.json"
    artifact.parent.mkdir(exist_ok=True)
    artifact.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(transcript.getvalue(), end="")
    print(f"Evidence: {artifact.relative_to(ROOT)}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
