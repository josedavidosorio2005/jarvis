from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile


def register(jarvis):
    jarvis.add_command(r"^ejecuta python (.+)$", run_python_code)


def run_python_code(match: re.Match):
    from jarvis import ActionResult

    if os.environ.get("JARVIS_ENABLE_GOD_MODE") != "1":
        return ActionResult(
            False,
            "Modo desarrollador bloqueado. Define JARVIS_ENABLE_GOD_MODE=1 y ejecuta desde consola para usarlo.",
        )

    code = match.group(1).strip()
    code = code.replace("\\n", "\n").replace("\\t", "\t")
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()

    blocked = ("import os", "import shutil", "subprocess", "remove", "rmdir", "unlink", "format", "shutdown")
    lowered = code.lower()
    if any(token in lowered for token in blocked):
        return ActionResult(False, "Codigo Python bloqueado por politica de seguridad.")

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, "-I", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout.strip()
        error = result.stderr.strip()
        if len(output) > 1200:
            output = output[:1200] + "\n..."
        if len(error) > 1200:
            error = error[:1200] + "\n..."

        if result.returncode == 0:
            return ActionResult(True, f"Codigo Python ejecutado.\nSalida: {output or '(sin salida)'}")
        return ActionResult(False, f"Error ejecutando codigo Python.\nSalida: {output}\nError: {error}")
    except Exception as exc:
        return ActionResult(False, f"Fallo en modo desarrollador: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
