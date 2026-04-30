from __future__ import annotations
import re
import sys
import subprocess
import tempfile
import os

def register(jarvis):
    # Se agrega con alta prioridad para que procese el comando correctamente
    jarvis.add_command(r"^ejecuta python (.+)$", run_python_code)

def run_python_code(match: re.Match):
    from jarvis import ActionResult
    code = match.group(1).strip()
    
    # Limpiamos el código por si la IA lo manda con etiquetas markdown
    code = code.replace("\\n", "\n").replace("\\t", "\t")
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Ocultar la ventana de consola si se requiere puede requerir flags adicionales en Windows,
        # pero subprocess.run la corre en background por defecto en el proceso actual.
        os.remove(tmp_path)
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if result.returncode == 0:
            return ActionResult(True, f"Código Python ejecutado exitosamente.\nSalida: {output}")
        else:
            return ActionResult(False, f"Error ejecutando código Python.\nSalida: {output}\nError: {error}")
            
    except Exception as e:
        return ActionResult(False, f"Fallo crítico en el Modo Dios: {e}")
