#!/usr/bin/env python3
"""Runtime verification for the Jarvis Windows assistant."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class CheckRunner:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def ok(self, name: str) -> None:
        print(f"[OK] {name}")

    def warn(self, name: str, message: str) -> None:
        self.warnings.append(f"{name}: {message}")
        print(f"[WARN] {name}: {message}")

    def fail(self, name: str, message: str) -> None:
        self.failures.append(f"{name}: {message}")
        print(f"[FAIL] {name}: {message}")

    def check(self, name: str, fn) -> None:
        try:
            fn()
            self.ok(name)
        except WarningError as exc:
            self.warn(name, str(exc))
        except Exception as exc:
            self.fail(name, str(exc))


class WarningError(Exception):
    pass


def assert_imports() -> None:
    required = [
        "pyautogui",
        "pyperclip",
        "psutil",
        "requests",
        "pyttsx3",
        "speech_recognition",
        "customtkinter",
        "pystray",
        "PIL",
        "pygetwindow",
    ]
    missing = []
    for module in required:
        try:
            importlib.import_module(module)
        except Exception as exc:
            missing.append(f"{module} ({exc})")
    if missing:
        raise RuntimeError("Faltan dependencias: " + ", ".join(missing))


def assert_config() -> None:
    example = ROOT / "config.example.json"
    if not example.exists():
        raise RuntimeError("Falta config.example.json")
    config = json.loads(example.read_text(encoding="utf-8"))
    for key in ("assistant_name", "wake_word", "fallback_provider", "ollama_model"):
        if key not in config:
            raise RuntimeError(f"config.example.json no define {key}")


def assert_main_imports() -> None:
    sys.path.insert(0, str(ROOT))
    jarvis = importlib.import_module("jarvis")
    gui = importlib.import_module("gui")
    if not hasattr(jarvis, "Jarvis") or not hasattr(jarvis, "ActionResult"):
        raise RuntimeError("jarvis.py no exporta Jarvis/ActionResult")
    if not hasattr(gui, "JarvisGUI") or not hasattr(gui, "main"):
        raise RuntimeError("gui.py no exporta JarvisGUI/main")


def assert_core_commands() -> None:
    sys.path.insert(0, str(ROOT))
    from jarvis import Jarvis

    app = Jarvis(speak=False, auto_confirm=False)
    checks = {
        "hora": "Son las",
        "fecha": "Hoy es",
    }
    for command, expected in checks.items():
        result = app.execute(command)
        if not result.ok:
            raise RuntimeError(f"{command!r} fallo: {result.message}")
        if expected.lower() not in result.message.lower():
            raise RuntimeError(f"{command!r} devolvio respuesta inesperada: {result.message}")
    for command in ("abre gmail", "abre whatsapp", "recordatorio revisar hoy a las 10"):
        if not app.has_direct_command(command):
            raise RuntimeError(f"{command!r} no esta registrado")


def assert_security_defaults() -> None:
    sys.path.insert(0, str(ROOT))
    from jarvis import Jarvis, requires_user_confirmation

    app = Jarvis(speak=False, auto_confirm=False)
    unknown = app.execute("abre esto-no-debe-ejecutarse-como-shell")
    if unknown.ok:
        raise RuntimeError("open_target acepta comandos desconocidos como shell")
    if not requires_user_confirmation("ejecuta powershell Remove-Item C:\\temp -Recurse"):
        raise RuntimeError("PowerShell peligroso no exige confirmacion")


def assert_voice_listener_present() -> None:
    if getattr(sys, "frozen", False):
        importlib.import_module("voice_listener_py")
        return
    listener = ROOT / "voice_listener_py.py"
    if not listener.exists():
        raise RuntimeError("Falta voice_listener_py.py")
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(listener)],
        check=True,
        capture_output=True,
        text=True,
    )


def assert_ollama_reachable() -> None:
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=2)
    except Exception as exc:
        raise WarningError(f"Ollama no responde localmente: {exc}")
    if response.status_code >= 400:
        raise WarningError(f"Ollama respondio HTTP {response.status_code}")


def main() -> int:
    print("=" * 56)
    print("VERIFICACION PROFESIONAL - JARVIS")
    print("=" * 56)

    runner = CheckRunner()
    runner.check("Dependencias Python", assert_imports)
    runner.check("Config de ejemplo", assert_config)
    runner.check("Imports principales", assert_main_imports)
    runner.check("Comandos principales y plugins", assert_core_commands)
    runner.check("Seguridad por defecto", assert_security_defaults)
    runner.check("Listener de voz", assert_voice_listener_present)
    runner.check("Ollama local", assert_ollama_reachable)

    print("=" * 56)
    if runner.failures:
        print("FALLAS:")
        for failure in runner.failures:
            print(f"  - {failure}")
    if runner.warnings:
        print("ADVERTENCIAS:")
        for warning in runner.warnings:
            print(f"  - {warning}")
    if runner.failures:
        print("Resultado: NO LISTO")
        return 1
    print("Resultado: LISTO" if not runner.warnings else "Resultado: LISTO CON ADVERTENCIAS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
