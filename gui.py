"""
Interfaz grafica futurista para Jarvis - Asistente Local.
(Migrada a customtkinter y pystray)
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
    from jarvis import MEMORY_FILE, Jarvis  # type: ignore

    JARVIS_AVAILABLE = True
except ImportError as exc:
    JARVIS_AVAILABLE = False
    IMPORT_ERROR = str(exc)
    MEMORY_FILE = ROOT / "memory.json"

CONFIG_FILE = ROOT / "config.json"


class JarvisGUI:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("JARVIS // Centro de Comando")
        self.root.geometry("1120x720")
        self.root.minsize(980, 620)
        
        # Colors
        self.colors = {
            "bg": "#070b10",
            "panel": "#0d1520",
            "cyan": "#18d8ff",
            "green": "#7cffb2",
            "rose": "#ff6b9d",
            "amber": "#ffd166",
            "danger": "#ff4d6d",
        }

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
                "Abrir",
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
                "Pantalla",
                [
                    ("Captura", "captura pantalla"),
                    ("Mirar pantalla", "mira pantalla"),
                    ("Ventana activa", "ventana activa"),
                    ("Maximizar", "maximiza ventana"),
                    ("Minimizar", "minimiza ventana"),
                    ("Cambiar ventana", "cambiar ventana"),
                ],
            ),
            (
                "IA",
                [
                    ("Planificar", "planifica "),
                    ("Autonomo", "haz "),
                    ("Buscar web", "busca "),
                    ("Recordar", "recuerda que "),
                    ("Tarea", "tarea "),
                    ("Decir", "decir "),
                ],
            ),
        ]

        self.setup_ui()
        self.write_system_status()
        self.root.after(1000, self.toggle_voice)

    def setup_ui(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_sidebar()
        self.build_chat()
        self.build_composer()

    def build_header(self) -> None:
        header = ctk.CTkFrame(self.root, height=80, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 0))
        header.grid_columnconfigure(1, weight=1)

        title_lbl = ctk.CTkLabel(header, text="JARVIS // CORE", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=self.colors["cyan"])
        title_lbl.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(header, text="INICIANDO", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color=self.colors["amber"])
        self.status_label.grid(row=0, column=1, sticky="e")

    def build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=10)
        sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=20, pady=20)
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="FUNCIONES", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))

        tools_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        tools_frame.pack(fill="both", expand=True, padx=10, pady=5)

        for group, commands in self.quick_commands:
            ctk.CTkLabel(tools_frame, text=group.upper(), font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(anchor="w", pady=(10, 5))
            grid = ctk.CTkFrame(tools_frame, fg_color="transparent")
            grid.pack(fill="x")
            grid.grid_columnconfigure((0, 1), weight=1)

            for index, (label, command) in enumerate(commands):
                btn = ctk.CTkButton(grid, text=label, command=lambda cmd=command: self.quick_action(cmd), height=30, 
                                    fg_color="#1f2937", hover_color="#374151")
                btn.grid(row=index // 2, column=index % 2, sticky="ew", padx=2, pady=2)

        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkButton(bottom, text="Voz", command=self.toggle_voice, fg_color="#9f1239", hover_color="#be123c").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(bottom, text="Config", command=self.open_config, fg_color="#b45309", hover_color="#d97706").pack(side="left", fill="x", expand=True, padx=(5, 0))

    def build_chat(self) -> None:
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Canal de ejecucion", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")
        self.busy_label = ctk.CTkLabel(header, text="LISTO", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color=self.colors["green"])
        self.busy_label.grid(row=0, column=1, sticky="e")

        self.chat_area = ctk.CTkTextbox(main, font=ctk.CTkFont(family="Consolas", size=14), wrap="word", corner_radius=10)
        self.chat_area.grid(row=1, column=0, sticky="nsew")
        self.chat_area.configure(state="disabled")

    def build_composer(self) -> None:
        composer = ctk.CTkFrame(self.root, corner_radius=10)
        composer.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=(0, 20))
        composer.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(composer, font=ctk.CTkFont(size=14), placeholder_text="Escribe un comando...", height=40)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.input_entry.bind("<Return>", lambda _event: self.send_command())
        self.input_entry.focus_set()

        self.send_btn = ctk.CTkButton(composer, text="Enviar", command=self.send_command, width=80, height=40)
        self.send_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        ctk.CTkButton(composer, text="Limpiar", command=self.clear_chat, fg_color="#374151", hover_color="#4b5563", width=80, height=40).grid(row=0, column=2, padx=(0, 10), pady=10)

    def write_system_status(self) -> None:
        self.add_message("system", "Jarvis GUI cargada. Escribe un comando o usa los accesos rapidos.")
        if JARVIS_AVAILABLE:
            self.status_label.configure(text="NUCLEO ONLINE", text_color=self.colors["green"])
            self.add_message("system", "Modulo Jarvis disponible. Todas las funciones locales estan conectadas.")
        else:
            self.status_label.configure(text="SIN NUCLEO", text_color=self.colors["danger"])
            self.add_message("error", f"No se pudo importar jarvis.py: {IMPORT_ERROR}")

    def add_message(self, tag: str, message: str) -> None:
        self.chat_area.configure(state="normal")
        prefix = ""
        if tag == "user": prefix = "TU > "
        elif tag == "jarvis": prefix = "JARVIS > "
        elif tag == "error": prefix = "ERROR > "
        elif tag == "system": prefix = "SYSTEM > "
        
        self.chat_area.insert("end", f"{prefix}{message.strip()}\n\n")
        self.chat_area.see("end")
        self.chat_area.configure(state="disabled")

    def clear_chat(self) -> None:
        self.chat_area.configure(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.configure(state="disabled")
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
            self.add_message("system", "Jarvis esta ocupado. Espera un momento.")
            return

        self.processing = True
        self.set_busy(True)
        self.add_message("user", command)

        thread = threading.Thread(target=self.process_command, args=(command,), daemon=True)
        thread.start()

    def process_command(self, command: str) -> None:
        try:
            if not JARVIS_AVAILABLE:
                self.root.after(0, lambda: self.add_message("error", "No se pudo cargar jarvis.py."))
                return

            if self.jarvis is None:
                self.jarvis = Jarvis(speak=False, auto_confirm=True)

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
            text="EJECUTANDO" if busy else "LISTO",
            text_color=self.colors["amber"] if busy else self.colors["green"],
        )
        self.send_btn.configure(state="disabled" if busy else "normal")

    def toggle_voice(self) -> None:
        if self.voice_process and self.voice_process.poll() is None:
            self.voice_process.terminate()
            self.voice_process = None
            self.add_message("system", "Modo voz detenido.")
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
            self.add_message("system", "Modo voz iniciado en segundo plano. Sigue funcionando aunque cierres la ventana (System Tray).")
            threading.Thread(target=self.monitor_voice_process, daemon=True).start()
        except Exception as exc:
            messagebox.showerror("Modo voz", f"No pude iniciar el modo voz:\n{exc}")

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
        self.root.after(0, lambda: self.add_message("system", "Modo voz finalizo."))

    def open_config(self) -> None:
        choice = simpledialog.askstring(
            "Config / PowerShell",
            "Escribe una accion:\n"
            "- config: abrir config.json\n"
            "- memoria: abrir memory.json\n"
            "- ps <comando>: ejecutar PowerShell",
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
            self.run_command("ejecuta powershell " + value[3:].strip())
        else:
            self.add_message("system", "Accion no reconocida. Usa config, memoria o ps <comando>.")

    def open_file(self, path: Path) -> None:
        try:
            if not path.exists():
                path.write_text("{}\n", encoding="utf-8")
            os.startfile(path)
            self.add_message("system", f"Abriendo {path.name}.")
        except Exception as exc:
            messagebox.showerror("Abrir archivo", f"No pude abrir {path}:\n{exc}")

    # --- System Tray Integration ---
    def create_tray_image(self) -> Image.Image:
        image = Image.new('RGB', (64, 64), color=(7, 11, 16))
        dc = ImageDraw.Draw(image)
        dc.ellipse((10, 10, 54, 54), outline=(24, 216, 255), width=4)
        dc.ellipse((22, 22, 42, 42), outline=(124, 255, 178), width=4)
        return image

    def setup_tray(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Abrir Jarvis", self.show_window),
            pystray.MenuItem("Salir", self.quit_app)
        )
        self.tray_icon = pystray.Icon("Jarvis", self.create_tray_image(), "Jarvis (Escuchando...)", menu)
        self.tray_icon.run()

    def hide_window(self) -> None:
        self.root.withdraw()
        self.add_message("system", "Ventana oculta. Jarvis sigue escuchando en segundo plano. Usa el icono junto al reloj para abrir o salir.")

    def show_window(self, icon, item) -> None:
        self.root.after(0, self.root.deiconify)

    def quit_app(self, icon, item) -> None:
        if self.tray_icon:
            self.tray_icon.stop()
        if self.voice_process and self.voice_process.poll() is None:
            self.voice_process.terminate()
        self.root.after(0, self.root.destroy)


def main() -> None:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    app = JarvisGUI(root)
    
    root.protocol("WM_DELETE_WINDOW", app.hide_window)
    threading.Thread(target=app.setup_tray, daemon=True).start()
    
    root.mainloop()


if __name__ == "__main__":
    main()
