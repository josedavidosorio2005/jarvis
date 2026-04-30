"""
Interfaz grafica futurista para Jarvis - Asistente Local.
(Rediseñada para despliegue profesional)
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path

import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

try:
    from jarvis import MEMORY_FILE, Jarvis, requires_user_confirmation  # type: ignore

    JARVIS_AVAILABLE = True
except ImportError as exc:
    JARVIS_AVAILABLE = False
    IMPORT_ERROR = str(exc)
    MEMORY_FILE = ROOT / "memory.json"

    def requires_user_confirmation(_: str) -> bool:
        return False

CONFIG_FILE = ROOT / "config.json"


class JarvisGUI:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("JARVIS // Command Center")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Paleta de colores Premium
        self.colors = {
            "bg": "#0B0F19",             # Fondo profundo oscuro
            "panel": "#151B2B",          # Paneles laterales
            "cyan": "#00F0FF",           # Detalles neon cyan
            "green": "#00FF9D",          # Éxito / Online
            "rose": "#FF0055",           # Peligro / Error alternativo
            "amber": "#FFB800",          # Ocupado / Advertencia
            "danger": "#FF3366",         # Error crítico
            "chat_user": "#1E3A8A",      # Burbuja usuario
            "chat_jarvis": "#1A2235",    # Burbuja Jarvis
            "chat_system": "transparent"
        }

        self.root.configure(fg_color=self.colors["bg"])

        self.jarvis: Jarvis | None = None
        self.processing = False
        self.voice_process: subprocess.Popen[str] | None = None
        self.tray_icon = None

        self.quick_commands: list[tuple[str, list[tuple[str, str]]]] = [
            (
                "Sistema",
                [
                    ("Ayuda", "ayuda"),
                    ("Hora", "hora"),
                    ("Fecha", "fecha"),
                    ("Limpiar", "limpia sistema"),
                    ("Procesos", "lista procesos"),
                    ("Memoria", "que recuerdas"),
                ],
            ),
            (
                "Aplicaciones",
                [
                    ("Calculadora", "abre calculadora"),
                    ("Bloc notas", "abre bloc de notas"),
                    ("Gmail", "abre gmail"),
                    ("WhatsApp", "abre whatsapp"),
                    ("Calendario", "abre calendario"),
                    ("Spotify", "abre spotify"),
                ],
            ),
            (
                "Pantalla & Ventanas",
                [
                    ("Captura", "captura pantalla"),
                    ("Mirar", "mira pantalla"),
                    ("Activa", "ventana activa"),
                    ("Maximizar", "maximiza ventana"),
                    ("Minimizar", "minimiza ventana"),
                    ("Cambiar", "cambiar ventana"),
                ],
            ),
            (
                "Modo Autónomo (IA)",
                [
                    ("Planificar", "planifica "),
                    ("Ejecutar", "haz "),
                    ("Buscar", "busca "),
                    ("Recordar", "recuerda que "),
                    ("Tarea", "tarea "),
                    ("Decir", "decir "),
                ],
            ),
        ]

        self.setup_ui()
        self.write_system_status()
        self.refresh_runtime_status()

    def setup_ui(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_sidebar()
        self.build_chat()
        self.build_composer()

    def build_header(self) -> None:
        header = ctk.CTkFrame(self.root, height=70, fg_color=self.colors["panel"], corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Contenedor del título con logo simulado
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=25, pady=15)
        
        logo_lbl = ctk.CTkLabel(title_frame, text="⬡", font=ctk.CTkFont(size=30, weight="bold"), text_color=self.colors["cyan"])
        logo_lbl.pack(side="left", padx=(0, 10))

        title_lbl = ctk.CTkLabel(title_frame, text="JARVIS", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color="#FFFFFF")
        title_lbl.pack(side="left")
        
        subtitle_lbl = ctk.CTkLabel(title_frame, text="// CORE", font=ctk.CTkFont(family="Segoe UI", size=14), text_color=self.colors["cyan"])
        subtitle_lbl.pack(side="left", padx=(5, 0), pady=(8, 0))

        # Status
        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.grid(row=0, column=1, sticky="e", padx=25)
        
        self.status_dot = ctk.CTkLabel(status_frame, text="●", font=ctk.CTkFont(size=18), text_color=self.colors["amber"])
        self.status_dot.pack(side="left", padx=(0, 8))
        
        self.status_label = ctk.CTkLabel(status_frame, text="INICIANDO SISTEMA", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#A0AABF")
        self.status_label.pack(side="left")

    def build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self.root, width=280, fg_color=self.colors["panel"], corner_radius=0)
        sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="PANEL DE CONTROL", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="#5E6A82").pack(anchor="w", padx=25, pady=(25, 10))

        tools_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", scrollbar_button_color="#2A3441", scrollbar_button_hover_color="#3B4758")
        tools_frame.pack(fill="both", expand=True, padx=15, pady=5)

        for group, commands in self.quick_commands:
            group_frame = ctk.CTkFrame(tools_frame, fg_color="transparent")
            group_frame.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(group_frame, text=group.upper(), font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#5E6A82").pack(anchor="w", padx=5, pady=(0, 5))
            
            grid = ctk.CTkFrame(group_frame, fg_color="transparent")
            grid.pack(fill="x")
            grid.grid_columnconfigure((0, 1), weight=1)

            for index, (label, command) in enumerate(commands):
                btn = ctk.CTkButton(
                    grid, text=label, command=lambda cmd=command: self.quick_action(cmd),
                    height=32, fg_color="#1E2638", hover_color="#2A3441",
                    font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#D1D5DB",
                    corner_radius=6
                )
                btn.grid(row=index // 2, column=index % 2, sticky="ew", padx=3, pady=3)

        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=20)
        
        # Botones inferiores estilizados
        self.btn_voice = ctk.CTkButton(
            bottom, text="Activar Voz", command=self.toggle_voice,
            fg_color="#9F1239", hover_color="#BE123C",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), height=40, corner_radius=8
        )
        self.btn_voice.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(
            bottom, text="Configuración", command=self.open_config,
            fg_color="#2A3441", hover_color="#3B4758",
            font=ctk.CTkFont(family="Segoe UI", size=13), height=40, corner_radius=8
        ).pack(fill="x")

    def build_chat(self) -> None:
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.grid(row=1, column=1, sticky="nsew", padx=30, pady=(25, 10))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Registro de Ejecución", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="#FFFFFF").grid(row=0, column=0, sticky="w")
        
        self.busy_label = ctk.CTkLabel(header, text="ESPERANDO ÓRDENES", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=self.colors["green"])
        self.busy_label.grid(row=0, column=1, sticky="e")

        # Chat visual premium
        self.chat_area = ctk.CTkScrollableFrame(main, fg_color="transparent", scrollbar_button_color="#2A3441")
        self.chat_area.grid(row=1, column=0, sticky="nsew")

    def build_composer(self) -> None:
        composer_container = ctk.CTkFrame(self.root, fg_color="transparent")
        composer_container.grid(row=2, column=1, sticky="ew", padx=30, pady=(0, 25))
        composer_container.grid_columnconfigure(0, weight=1)

        composer = ctk.CTkFrame(composer_container, fg_color=self.colors["panel"], corner_radius=12, border_width=1, border_color="#2A3441")
        composer.grid(row=0, column=0, sticky="ew")
        composer.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            composer, font=ctk.CTkFont(family="Segoe UI", size=15),
            placeholder_text="Escribe un comando para Jarvis...", 
            height=55, fg_color="transparent", border_width=0, text_color="#FFFFFF",
            placeholder_text_color="#5E6A82"
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=20, pady=5)
        self.input_entry.bind("<Return>", lambda _event: self.send_command())
        self.input_entry.focus_set()

        self.send_btn = ctk.CTkButton(
            composer, text="ENVIAR", command=self.send_command,
            width=100, height=40, fg_color=self.colors["cyan"], hover_color="#00C4D1",
            text_color="#0B0F19", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            corner_radius=8
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 15), pady=10)

        ctk.CTkButton(
            composer_container, text="LIMPIAR", command=self.clear_chat,
            fg_color="transparent", hover_color="#1E2638", border_width=1, border_color="#2A3441",
            width=80, height=55, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#A0AABF", corner_radius=12
        ).grid(row=0, column=1, padx=(15, 0))

    def write_system_status(self) -> None:
        self.add_message("system", "Interfaz principal cargada. Esperando comandos.")
        if JARVIS_AVAILABLE:
            self.status_label.configure(text="SISTEMA ONLINE")
            self.status_dot.configure(text_color=self.colors["green"])
            self.add_message("system", "Modulo Jarvis conectado. Voz desactivada hasta que la actives manualmente.")
        else:
            self.status_label.configure(text="SISTEMA OFFLINE")
            self.status_dot.configure(text_color=self.colors["danger"])
            self.add_message("error", f"Error critico al iniciar Jarvis: {IMPORT_ERROR}")

    def refresh_runtime_status(self) -> None:
        checks = []
        checks.append("OpenAI: listo" if os.environ.get("OPENAI_API_KEY") else "OpenAI: sin clave")
        try:
            import requests

            response = requests.get("http://localhost:11434/api/tags", timeout=1.5)
            checks.append("Ollama: online" if response.status_code < 400 else f"Ollama: HTTP {response.status_code}")
        except Exception:
            checks.append("Ollama: offline")
        checks.append("Microfono: activar para probar")
        self.add_message("system", "Estado: " + " | ".join(checks))

    def add_message(self, tag: str, message: str) -> None:
        frame = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        frame.pack(fill="x", pady=8, padx=5)
        
        if tag == "user":
            bubble_color = self.colors["chat_user"]
            align = "e"
            text_color = "#FFFFFF"
            prefix = "USUARIO"
            prefix_color = "#93C5FD"
        elif tag == "jarvis":
            bubble_color = self.colors["chat_jarvis"]
            align = "w"
            text_color = self.colors["cyan"]
            prefix = "JARVIS"
            prefix_color = "#5E6A82"
        elif tag == "error":
            bubble_color = "#2E1114"
            align = "w"
            text_color = self.colors["danger"]
            prefix = "ERROR"
            prefix_color = "#FCA5A5"
        else:
            bubble_color = "transparent"
            align = "w"
            text_color = "#A0AABF"
            prefix = "SISTEMA"
            prefix_color = "#5E6A82"
            
        bubble = ctk.CTkFrame(frame, fg_color=bubble_color, corner_radius=12)
        bubble.pack(side="right" if align == "e" else "left", padx=10, ipadx=10, ipady=8, fill="x", expand=False)
        
        # Ajustar wraplength basado en tamaño de ventana
        max_width = 700
        
        if tag != "system":
            lbl_prefix = ctk.CTkLabel(bubble, text=prefix, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=prefix_color)
            lbl_prefix.pack(anchor="w" if align == "w" else "e", padx=5, pady=(2, 2))
        
        lbl_msg = ctk.CTkLabel(
            bubble, text=message.strip(), font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=text_color, justify="left" if align == "w" else "right", wraplength=max_width
        )
        lbl_msg.pack(anchor="w" if align == "w" else "e", padx=5, pady=(0, 2))

        self.root.after(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        try:
            self.chat_area._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def clear_chat(self) -> None:
        for widget in self.chat_area.winfo_children():
            widget.destroy()
        self.write_system_status()

    def quick_action(self, command: str) -> None:
        if command.endswith(" "):
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, command)
            self.input_entry.focus_set()
            return
        self.run_command(command)

    def send_command(self) -> None:
        command = self.input_entry.get().strip()
        if not command:
            return
        self.input_entry.delete(0, "end")
        self.run_command(command)

    def run_command(self, command: str) -> None:
        if self.processing:
            self.add_message("system", "Proceso en curso. Por favor espere.")
            return

        self.processing = True
        self.set_busy(True)
        self.add_message("user", command)

        thread = threading.Thread(target=self.process_command, args=(command,), daemon=True)
        thread.start()

    def process_command(self, command: str) -> None:
        try:
            if not JARVIS_AVAILABLE:
                self.root.after(0, lambda: self.add_message("error", "Subsistema principal desconectado."))
                return

            if self.jarvis is None:
                self.jarvis = Jarvis(speak=False, auto_confirm=False)

            if requires_user_confirmation(command):
                self.root.after(
                    0,
                    lambda: self.add_message(
                        "error",
                        "Este comando requiere confirmacion por seguridad. Ejecutalo desde PowerShell con .\\run.ps1.",
                    ),
                )
                return

            result = self.jarvis.execute(command)
            tag = "jarvis" if result.ok else "error"
            self.root.after(0, lambda: self.add_message(tag, result.message))
        except Exception as exc:
            self.root.after(0, lambda: self.add_message("error", str(exc)))
        finally:
            self.root.after(0, lambda: self.set_busy(False))
            self.processing = False

    def set_busy(self, busy: bool) -> None:
        self.processing = busy
        self.busy_label.configure(
            text="PROCESANDO" if busy else "ESPERANDO ÓRDENES",
            text_color=self.colors["amber"] if busy else self.colors["green"],
        )
        self.send_btn.configure(state="disabled" if busy else "normal")

    def toggle_voice(self) -> None:
        if self.voice_process and self.voice_process.poll() is None:
            self.voice_process.terminate()
            self.voice_process = None
            self.btn_voice.configure(text="Activar Voz", fg_color="#9F1239", hover_color="#BE123C")
            self.add_message("system", "Módulo de reconocimiento de voz desactivado.")
            return

        try:
            self.voice_process = subprocess.Popen(
                [sys.executable, str(ROOT / "jarvis.py"), "--voice"],
                cwd=str(ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
            )
            self.btn_voice.configure(text="Desactivar Voz", fg_color=self.colors["green"], text_color="#000000", hover_color="#00D180")
            self.add_message("system", "Módulo de voz activo (Escuchando en segundo plano).")
            threading.Thread(target=self.monitor_voice_process, daemon=True).start()
        except Exception as exc:
            messagebox.showerror("Módulo de Voz", f"Error de inicialización:\n{exc}")

    def monitor_voice_process(self) -> None:
        if not self.voice_process or not self.voice_process.stdout:
            return
        for line in self.voice_process.stdout:
            text = line.strip()
            if text:
                if "Tu voz:" in text:
                    self.root.after(0, lambda t=text: self.add_message("user", t.replace("Tu voz: ", "")))
                elif "Jarvis:" in text:
                    self.root.after(0, lambda t=text: self.add_message("jarvis", t.replace("Jarvis: ", "")))
                else:
                    self.root.after(0, lambda t=text: self.add_message("system", t))
        
        # Reset button if process dies
        self.root.after(0, lambda: self.btn_voice.configure(text="Activar Voz", fg_color="#9F1239", text_color="#FFFFFF", hover_color="#BE123C"))
        self.root.after(0, lambda: self.add_message("system", "El módulo de voz ha finalizado."))

    def open_config(self) -> None:
        choice = simpledialog.askstring(
            "Consola de Administración",
            "Ingrese comando de sistema:\n\n"
            "> config  (Abrir configuración)\n"
            "> memoria (Ver datos persistentes)\n"
            "> ps cmd  (Ejecutar script de PowerShell)",
        )
        if not choice:
            return
        value = choice.strip()
        lower = value.lower()

        if lower == "config":
            self.open_file(CONFIG_FILE)
        elif lower == "memoria":
            self.open_file(MEMORY_FILE)
        elif lower.startswith("ps "):
            self.add_message("error", "PowerShell directo esta bloqueado en la GUI. Usa .\\run.ps1 para confirmar.")
        else:
            self.add_message("error", "Comando no reconocido en la consola administrativa.")

    def open_file(self, path: Path) -> None:
        try:
            if not path.exists():
                path.write_text("{}\n", encoding="utf-8")
            os.startfile(path)
            self.add_message("system", f"Abriendo recurso: {path.name}")
        except Exception as exc:
            messagebox.showerror("Error I/O", f"No se pudo acceder al recurso {path}:\n{exc}")

    # --- System Tray Integration ---
    def create_tray_image(self) -> Image.Image:
        image = Image.new('RGB', (64, 64), color=(11, 15, 25))
        dc = ImageDraw.Draw(image)
        dc.ellipse((10, 10, 54, 54), outline=(0, 240, 255), width=4)
        dc.ellipse((22, 22, 42, 42), outline=(0, 255, 157), width=4)
        return image

    def setup_tray(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Desplegar Centro de Comando", self.show_window, default=True),
            pystray.MenuItem("Apagar Sistema", self.quit_app)
        )
        self.tray_icon = pystray.Icon("Jarvis", self.create_tray_image(), "JARVIS // Sistema Operativo", menu)
        self.tray_icon.run()

    def hide_window(self) -> None:
        self.root.withdraw()
        self.add_message("system", "Modo silencioso activado. Jarvis operará desde la bandeja del sistema.")

    def show_window(self, icon, item) -> None:
        self.root.after(0, self.root.deiconify)
        self.root.after(0, lambda: self.add_message("system", "Interfaz restaurada."))

    def quit_app(self, icon, item) -> None:
        if self.tray_icon:
            self.tray_icon.stop()
        if self.voice_process and self.voice_process.poll() is None:
            self.voice_process.terminate()
        self.root.after(0, self.root.destroy)


def main() -> None:
    # Configuración base de ctk
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    app = JarvisGUI(root)
    
    # Interceptar cierre para ocultar
    root.protocol("WM_DELETE_WINDOW", app.hide_window)
    
    # Iniciar System Tray
    threading.Thread(target=app.setup_tray, daemon=True).start()
    
    root.mainloop()


if __name__ == "__main__":
    main()
