#!/usr/bin/env python3
"""Run every bundled competitor-tracker test without network access."""

import pathlib
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent


def main():
    subprocess.run([sys.executable, str(HERE / "test_guards.py")], cwd=HERE.parent, check=True)
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_tracker.py", "-v"],
        cwd=HERE.parent,
        check=True,
    )


if __name__ == "__main__":
    main()
