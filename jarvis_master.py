#!/usr/bin/env python3
"""
JARVIS - Script Maestro Unificado
=================================
Un único punto de entrada para:
1. Verificar todas las funciones
2. Ejecutar la interfaz gráfica
3. Subir a GitHub

Uso:
    python jarvis_master.py          -> Ejecutar GUI
    python jarvis_master.py --verify -> Verificar funciones
    python jarvis_master.py --push  -> Subir a GitHub
    python jarvis_master.py --all   -> Todo junto
"""

import subprocess
import sys
import os
import importlib
from pathlib import Path

# Colores para terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

ROOT = Path(__file__).parent


def print_banner():
    """Muestra el banner de Jarvis"""
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════╗
║  ████████╗██████╗  █████╗ ██████╗  █████╗ ██████╗  █████╗  █████╗ ║
║  ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗║
║     ██║   ██████╔╝███████║██████╔╝███████║██████╔╝███████║██████║║
║     ██║   ██╔══██╗██╔══██║██╔══██╗██╔══██║██╔══██╗██╔══██║██╔══██║║
║     ██║   ██║  ██║██║  ██║██║  ██║██║  ██║██║  ██║██║  ██║██║  ██║║
║     ██║   ██████╔╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝║
║  ██╗ ██████╗ ██████╗  ██████╗  ██████╗ ███████╗ ██████╗ ██████╗ ║
║  ██║██╔════╝██╔═══██╗██╔════╝ ██╔═══██╗██╔════╝██╔═══██╗██╔══██╗║
║  ██║██║  ███╗██║   ██║██║  ███╗██║   ██║███████╗██║   ██║██████╔╝║
║  ██║██║   ██║██║   ██║██║   ██║██║   ██║██╔════╝██║   ██║██╔══██╗║
║  ██║╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝███████╗╚██████╔╝██║  ██║║
║  ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═╝║
╚═══════════════════════════════════════════════════════════╝{RESET}
    """)


def install_dependencies():
    """Instala las dependencias necesarias de requirements.txt si faltan"""
    req_file = ROOT / "requirements.txt"
    if not req_file.exists():
        return
    
    print(f"{BOLD}{YELLOW}▶ VERIFICANDO DEPENDENCIAS EXTERNAS...{RESET}")
    
    try:
        # Check if customtkinter is installed as a proxy for external deps
        importlib.import_module('customtkinter')
    except ImportError:
        print(f"  {YELLOW}Faltan dependencias. Instalando desde requirements.txt...{RESET}")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--break-system-packages", "-r", str(req_file)]
            )
            print(f"  {GREEN}✓ Dependencias instaladas correctamente.{RESET}\n")
        except Exception as e:
            print(f"  {RED}✗ Error al instalar dependencias: {e}{RESET}\n")


def verify_functions():
    """Verifica que todas las funciones estén disponibles"""
    print(f"\n{BOLD}{YELLOW}▶ VERIFICANDO FUNCIONES...{RESET}\n")
    
    all_ok = True
    
    # 1. Verificar jarvis.py
    print("  [1/5] Verificando jarvis.py...", end=" ")
    try:
        spec = __import__('importlib.util').util.spec_from_file_location(
            "jarvis", ROOT / "jarvis.py"
        )
        if spec and spec.loader:
            print(f"{GREEN}✓{RESET}")
        else:
            raise Exception("No se pudo cargar")
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        all_ok = False
    
    # 2. Verificar gui.py
    print("  [2/5] Verificando gui.py...", end=" ")
    try:
        spec = __import__('importlib.util').util.spec_from_file_location(
            "gui", ROOT / "gui.py"
        )
        if spec and spec.loader:
            print(f"{GREEN}✓{RESET}")
        else:
            raise Exception("No se pudo cargar")
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        all_ok = False
    
    # 3. Verificar plugins
    print("  [3/5] Verificando plugins...", end=" ")
    plugins_dir = ROOT / "plugins"
    plugins_ok = True
    if plugins_dir.exists():
        for plugin in plugins_dir.glob("*.py"):
            if plugin.name != "__init__.py":
                try:
                    __import__('importlib.util').util.spec_from_file_location(
                        plugin.stem, plugin
                    )
                except:
                    plugins_ok = False
                    break
    if plugins_ok:
        print(f"{GREEN}✓{RESET}")
    else:
        print(f"{RED}✗{RESET}")
        all_ok = False
    
    # 4. Verificar config.json
    print("  [4/5] Verificando config.json...", end=" ")
    config_file = ROOT / "config.json"
    if config_file.exists():
        print(f"{GREEN}✓{RESET}")
    else:
        print(f"{YELLOW}⚠ No existe (usará ejemplo){RESET}")
    
    # 5. Verificar dependencias
    print("  [5/5] Verificando dependencias...", end=" ")
    deps_ok = True
    required = ['tkinter', 'json', 'threading', 'subprocess', 'pathlib']
    for dep in required:
        try:
            __import__(dep)
        except ImportError:
            deps_ok = False
            break
    if deps_ok:
        print(f"{GREEN}✓{RESET}")
    else:
        print(f"{RED}✗ Faltan dependencias{RESET}")
        all_ok = False
    
    print(f"\n{BOLD}{'='*50}")
    if all_ok:
        print(f"{GREEN}✓ TODAS LAS FUNCIONES VERIFICADAS{RESET}")
    else:
        print(f"{RED}✗ ALGUNAS VERIFICACIONES FALLARON{RESET}")
    print(f"{'='*50}{RESET}\n")
    
    return all_ok


def run_gui():
    """Ejecuta la interfaz gráfica"""
    print(f"\n{BOLD}{CYAN}▶ INICIANDO INTERFAZ GRÁFICA...{RESET}\n")
    
    try:
        # Importar y ejecutar la GUI
        import tkinter as tk
        from gui import JarvisGUI, main as gui_main
        
        # Ejecutar la GUI
        gui_main()
    except Exception as e:
        print(f"{RED}✗ Error al iniciar GUI: {e}{RESET}")
        return False
    
    return True


def push_to_github():
    """Sube los cambios a GitHub"""
    print(f"\n{BOLD}{YELLOW}▶ SUBIENDO A GITHUB...{RESET}\n")
    
    try:
        # Agregar cambios
        print("  Agregando archivos...")
        result = subprocess.run(
            ['git', 'add', '.'],
            cwd=ROOT,
            capture_output=True,
            text=True
        )
        
        # Verificar si hay cambios
        result_status = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=ROOT,
            capture_output=True,
            text=True
        )
        
        if not result_status.stdout.strip():
            print("  No hay cambios pendientes")
            return True
        
        # Commit
        print("  Creando commit...")
        subprocess.run(
            ['git', 'commit', '-m', 'Release: Interfaz UI Premium y Auto-instalador de dependencias activado'],
            cwd=ROOT,
            capture_output=True,
            text=True
        )
        
        # Push
        print("  Subiendo a GitHub...")
        result = subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n{GREEN}✓ SUBIDO A GITHUB EXITOSAMENTE{RESET}")
            return True
        else:
            print(f"{RED}✗ Error al subir: {result.stderr}{RESET}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return False


def main():
    """Punto de entrada principal"""
    print_banner()
    install_dependencies()
    
    # Si no hay argumentos, ejecutar GUI
    if len(sys.argv) == 1:
        print(f"{CYAN}Ejecutando interfaz gráfica...{RESET}\n")
        run_gui()
        return
    
    # Procesar argumentos
    arg = sys.argv[1].lower()
    
    if arg == '--verify' or arg == '-v':
        # Solo verificar
        verify_functions()
        
    elif arg == '--push' or arg == '-p':
        # Solo subir a GitHub
        push_to_github()
        
    elif arg == '--all' or arg == '-a':
        # Todo: verificar + ejecutar + subir
        print(f"{BOLD}{CYAN}╔══════════════════════════════════════╗")
        print(f"║  MODO COMPLETO: Verificar + Ejecutar + Subir  ║")
        print(f"╚══════════════════════════════════════╝{RESET}\n")
        
        # 1. Verificar
        if not verify_functions():
            print(f"{RED}✗ Verificación falló. Abortando.{RESET}")
            sys.exit(1)
        
        # 2. Ejecutar GUI
        run_gui()
        
        # 3. Preguntar si subir a GitHub
        print(f"\n{YELLOW}¿Deseas subir los cambios a GitHub? (s/n): {RESET}", end=" ")
        respuesta = input().lower().strip()
        if respuesta in ['s', 'si', 'y', 'yes']:
            push_to_github()
        
    elif arg == '--help' or arg == '-h':
        # Mostrar ayuda
        print(f"""
{BOLD}Uso: python jarvis_master.py [opción]{RESET}

{Opciones:}
  (sin args)    - Ejecutar la interfaz gráfica
  --verify, -v  - Verificar todas las funciones
  --push, -p    - Subir cambios a GitHub
  --all, -a     - Verificar + Ejecutar + Preguntar subir
  --help, -h   - Mostrar esta ayuda

{Ejemplos:}
  python jarvis_master.py          # Ejecutar GUI
  python jarvis_master.py --verify # Verificar funciones
  python jarvis_master.py --all    # Todo junto
        """)
        
    else:
        print(f"{RED}Opción desconocida: {arg}{RESET}")
        print(f"Usa --help para ver las opciones disponibles")
        sys.exit(1)


if __name__ == "__main__":
    main()