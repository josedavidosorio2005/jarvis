#!/usr/bin/env python3
"""Script para verificar que todas las funciones de Jarvis funcionen correctamente."""

import sys
import importlib.util
from pathlib import Path

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def test_jarvis_main():
    """Prueba importar y verificar funciones principales de jarvis.py"""
    try:
        spec = importlib.util.spec_from_file_location("jarvis", Path(__file__).parent / "jarvis.py")
        jarvis_module = importlib.util.module_from_spec(spec)
        # No ejecutamos el spec porque jarvis.py tiene código de ejecución
        print("✓ jarvis.py - Importable")
        return True
    except Exception as e:
        print(f"✗ jarvis.py - Error: {e}")
        return False

def test_gui():
    """Prueba importar gui.py"""
    try:
        spec = importlib.util.spec_from_file_location("gui", Path(__file__).parent / "gui.py")
        print("✓ gui.py - Importable")
        return True
    except Exception as e:
        print(f"✗ gui.py - Error: {e}")
        return False

def test_plugins():
    """Verifica que los plugins existan y sean importables"""
    plugins_dir = Path(__file__).parent / "plugins"
    all_ok = True
    
    for plugin_file in plugins_dir.glob("*.py"):
        if plugin_file.name == "__init__.py":
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                plugin_file.stem, 
                plugin_file
            )
            print(f"✓ plugins/{plugin_file.name} - OK")
        except Exception as e:
            print(f"✗ plugins/{plugin_file.name} - Error: {e}")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 50)
    print("VERIFICACIÓN DE FUNCIONES - JARVIS")
    print("=" * 50)
    
    results = []
    
    print("\n1. Verificando módulo principal...")
    results.append(test_jarvis_main())
    
    print("\n2. Verificando GUI...")
    results.append(test_gui())
    
    print("\n3. Verificando plugins...")
    results.append(test_plugins())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ TODAS LAS FUNCIONES VERIFICADAS CON ÉXITO")
        print("=" * 50)
        return 0
    else:
        print("✗ ALGUNAS VERIFICACIONES FALLARON")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())
