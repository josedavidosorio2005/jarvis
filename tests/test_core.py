from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jarvis import Jarvis, MemoryStore, extract_due_at, normalize, requires_user_confirmation


def test_normalize_spanish_accents() -> None:
    assert normalize("JARVIS ábre calculadora") == "abre calculadora"


def test_memory_reminders(tmp_path: Path) -> None:
    memory = MemoryStore(tmp_path / "memory.json")
    memory.remember("mi color favorito es azul")
    memory.add_task("revisar manana a las 8")
    memory.add_reminder("tomar agua hoy a las 10")

    summary = memory.summary()
    assert "mi color favorito es azul" in summary
    assert "revisar manana" in summary
    assert "tomar agua" in memory.list_reminders()


def test_extract_due_at() -> None:
    assert extract_due_at("hoy a las 10") is not None
    assert extract_due_at("manana a las 7 de la noche") is not None
    assert extract_due_at("sin fecha") is None


def test_open_unknown_target_is_not_shell() -> None:
    app = Jarvis(speak=False, auto_confirm=False)
    result = app.execute("abre comando-inexistente-de-prueba")
    assert not result.ok


def test_security_confirmation_defaults() -> None:
    assert requires_user_confirmation("ejecuta powershell Get-Process")
    assert requires_user_confirmation("ejecuta powershell Remove-Item C:\\temp -Recurse")


def test_god_mode_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("JARVIS_ENABLE_GOD_MODE", raising=False)
    app = Jarvis(speak=False, auto_confirm=False)
    result = app.execute("ejecuta python print('hola')")
    assert not result.ok
    assert "bloqueado" in result.message.lower()
