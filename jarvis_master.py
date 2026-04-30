#!/usr/bin/env python3
"""Clean launcher for the Jarvis assistant."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


def python_executable() -> str:
    return str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def run_python_script(script: str, *args: str) -> int:
    return subprocess.call([python_executable(), str(ROOT / script), *args], cwd=ROOT)


def run_powershell_script(script: str) -> int:
    return subprocess.call(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / script)],
        cwd=ROOT,
    )


def run_gui() -> int:
    from gui import main as gui_main

    gui_main()
    return 0


def run_verify() -> int:
    from verify_functions import main as verify_main

    return verify_main()


def run_jarvis(*args: str) -> int:
    from jarvis import main as jarvis_main

    old_argv = sys.argv[:]
    try:
        sys.argv = ["jarvis.py", *args]
        return jarvis_main()
    finally:
        sys.argv = old_argv


def run_voice_listener(*args: str) -> int:
    from voice_listener_py import main as listener_main

    old_argv = sys.argv[:]
    try:
        sys.argv = ["voice_listener_py.py", *args]
        listener_main()
        return 0
    finally:
        sys.argv = old_argv


def main() -> int:
    parser = argparse.ArgumentParser(description="Jarvis professional launcher")
    parser.add_argument("--gui", action="store_true", help="Open the graphical command center.")
    parser.add_argument("--voice", action="store_true", help="Start Jarvis in voice mode.")
    parser.add_argument("--voice-listener", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--verify", action="store_true", help="Run runtime verification checks.")
    parser.add_argument("--setup", action="store_true", help="Install dependencies and prepare local runtime.")
    parser.add_argument("--package", action="store_true", help="Build the portable Windows package.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to send to Jarvis CLI.")
    args = parser.parse_args()

    if args.voice_listener:
        return run_voice_listener(*args.command)
    if args.setup:
        return run_powershell_script("setup_local.ps1")
    if args.verify:
        return run_verify()
    if args.package:
        return run_powershell_script("scripts\\build_portable.ps1")
    if args.gui or not args.command:
        return run_gui()
    if args.voice:
        return run_jarvis("--voice", *args.command)
    return run_jarvis(*args.command)


if __name__ == "__main__":
    raise SystemExit(main())
