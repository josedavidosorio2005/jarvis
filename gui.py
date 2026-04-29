"""
Interfaz grafica futurista para Jarvis - Asistente Local.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, simpledialog

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
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("JARVIS // Centro de Comando")
        self.root.geometry("1120x720")
        self.root.minsize(980, 620)
        self.root.configure(bg="#070b10")

        self.jarvis: Jarvis | None = None
        self.processing = False
        self.voice_process: subprocess.Popen[str] | None = None

        self.colors = {
            "bg": "#070b10",
            "panel": "#0d1520",
            "panel_2": "#111c29",
            "line": "#1f3a4b",
            "text": "#d8f3ff",
            "muted": "#7da4b7",
            "cyan": "#18d8ff",
            "green": "#7cffb2",
            "rose": "#ff6b9d",
            "amber": "#ffd166",
            "danger": "#ff4d6d",
        }

        self.quick_commands: list[tuple[str, list[tuple[str, str]]]] = [
            (
                "Sistema",
                [
                    ("Ayuda", "ayuda"),
                    ("Hora", "hora"),
                    ("Fecha", "fecha"),
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
                "Control",
                [
                    ("Clic", "clic"),
                    ("Doble clic", "doble clic"),
                    ("Clic derecho", "clic derecho"),
                    ("Enter", "presiona enter"),
                    ("Ctrl+L", "atajo ctrl l"),
                    ("Pegar", "pega portapapeles"),
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

    def setup_ui(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_sidebar()
        self.build_chat()
        self.build_composer()

    def build_header(self) -> None:
        header = tk.Frame(self.root, bg=self.colors["bg"], height=82)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        logo = tk.Canvas(header, width=68, height=68, bg=self.colors["bg"], highlightthickness=0)
        logo.grid(row=0, column=0, padx=(22, 12), pady=8)
        logo.create_oval(10, 10, 58, 58, outline=self.colors["cyan"], width=2)
        logo.create_oval(22, 22, 46, 46, outline=self.colors["green"], width=2)
        logo.create_line(34, 2, 34, 18, fill=self.colors["cyan"], width=2)
        logo.create_line(34, 50, 34, 66, fill=self.colors["cyan"], width=2)
        logo.create_line(2, 34, 18, 34, fill=self.colors["cyan"], width=2)
        logo.create_line(50, 34, 66, 34, fill=self.colors["cyan"], width=2)

        title_box = tk.Frame(header, bg=self.colors["bg"])
        title_box.grid(row=0, column=1, sticky="ew")
        tk.Label(
            title_box,
            text="JARVIS",
            font=("Segoe UI", 28, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"],
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="Centro de comando local para Windows",
            font=("Segoe UI", 10),
            fg=self.colors["muted"],
            bg=self.colors["bg"],
        ).pack(anchor="w")

        self.status_label = tk.Label(
            header,
            text="INICIANDO",
            font=("Consolas", 11, "bold"),
            fg=self.colors["amber"],
            bg=self.colors["panel"],
            padx=16,
            pady=8,
        )
        self.status_label.grid(row=0, column=2, padx=22)

    def build_sidebar(self) -> None:
        sidebar = tk.Frame(self.root, bg=self.colors["panel"], width=292)
        sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(18, 10), pady=(0, 18))
        sidebar.grid_propagate(False)

        tk.Label(
            sidebar,
            text="FUNCIONES",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["cyan"],
            bg=self.colors["panel"],
        ).pack(anchor="w", padx=16, pady=(16, 8))

        tools = tk.Frame(sidebar, bg=self.colors["panel"])
        tools.pack(fill=tk.BOTH, expand=True, padx=12)

        for group, commands in self.quick_commands:
            group_label = tk.Label(
                tools,
                text=group.upper(),
                font=("Segoe UI", 9, "bold"),
                fg=self.colors["muted"],
                bg=self.colors["panel"],
            )
            group_label.pack(anchor="w", pady=(12, 6))

            grid = tk.Frame(tools, bg=self.colors["panel"])
            grid.pack(fill=tk.X)
            grid.grid_columnconfigure(0, weight=1)
            grid.grid_columnconfigure(1, weight=1)

            for index, (label, command) in enumerate(commands):
                btn = self.neon_button(
                    grid,
                    label,
                    lambda cmd=command: self.quick_action(cmd),
                    accent=self.colors["cyan"] if index % 2 == 0 else self.colors["green"],
                )
                btn.grid(row=index // 2, column=index % 2, sticky="ew", padx=3, pady=3)

        bottom = tk.Frame(sidebar, bg=self.colors["panel"])
        bottom.pack(fill=tk.X, padx=12, pady=12)

        self.neon_button(bottom, "Voz", self.toggle_voice, accent=self.colors["rose"]).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        self.neon_button(bottom, "Config", self.open_config, accent=self.colors["amber"]).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0)
        )

    def build_chat(self) -> None:
        main = tk.Frame(self.root, bg=self.colors["bg"])
        main.grid(row=1, column=1, sticky="nsew", padx=(0, 18), pady=(0, 10))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        strip = tk.Frame(main, bg=self.colors["bg"])
        strip.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        strip.grid_columnconfigure(0, weight=1)
        tk.Label(
            strip,
            text="Canal de ejecucion",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"],
        ).grid(row=0, column=0, sticky="w")

        self.busy_label = tk.Label(
            strip,
            text="LISTO",
            font=("Consolas", 10, "bold"),
            fg=self.colors["green"],
            bg=self.colors["bg"],
        )
        self.busy_label.grid(row=0, column=1, sticky="e")

        chat_shell = tk.Frame(main, bg=self.colors["line"], padx=1, pady=1)
        chat_shell.grid(row=1, column=0, sticky="nsew")
        chat_shell.grid_columnconfigure(0, weight=1)
        chat_shell.grid_rowconfigure(0, weight=1)

        self.chat_area = scrolledtext.ScrolledText(
            chat_shell,
            font=("Consolas", 11),
            bg=self.colors["panel_2"],
            fg=self.colors["text"],
            insertbackground=self.colors["cyan"],
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            padx=14,
            pady=14,
        )
        self.chat_area.grid(row=0, column=0, sticky="nsew")
        self.chat_area.tag_config("user", foreground=self.colors["cyan"], spacing3=8)
        self.chat_area.tag_config("jarvis", foreground=self.colors["green"], spacing3=8)
        self.chat_area.tag_config("error", foreground=self.colors["danger"], spacing3=8)
        self.chat_area.tag_config("system", foreground=self.colors["muted"], spacing3=8)

    def build_composer(self) -> None:
        composer = tk.Frame(self.root, bg=self.colors["panel"], padx=12, pady=12)
        composer.grid(row=2, column=1, sticky="ew", padx=(0, 18), pady=(0, 18))
        composer.grid_columnconfigure(0, weight=1)

        self.input_entry = tk.Entry(
            composer,
            font=("Segoe UI", 13),
            bg="#08111a",
            fg=self.colors["text"],
            insertbackground=self.colors["cyan"],
            relief=tk.FLAT,
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", ipady=10, padx=(0, 8))
        self.input_entry.bind("<Return>", lambda _event: self.send_command())
        self.input_entry.focus_set()

        self.send_btn = self.neon_button(composer, "Enviar", self.send_command, accent=self.colors["green"])
        self.send_btn.grid(row=0, column=1, sticky="ns", padx=(0, 8))

        self.neon_button(composer, "Limpiar", self.clear_chat, accent=self.colors["rose"]).grid(
            row=0, column=2, sticky="ns"
        )

    def neon_button(self, parent: tk.Widget, text: str, command, accent: str) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["panel_2"],
            fg=accent,
            activebackground="#132535",
            activeforeground=self.colors["text"],
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
        )

    def write_system_status(self) -> None:
        self.add_message("system", "Jarvis GUI cargada. Escribe un comando o usa los accesos rapidos.")
        if JARVIS_AVAILABLE:
            self.status_label.config(text="NUCLEO ONLINE", fg=self.colors["green"])
            self.add_message("system", "Modulo Jarvis disponible. Todas las funciones locales estan conectadas.")
        else:
            self.status_label.config(text="SIN NUCLEO", fg=self.colors["danger"])
            self.add_message("error", f"No se pudo importar jarvis.py: {IMPORT_ERROR}")

    def add_message(self, tag: str, message: str) -> None:
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message.strip() + "\n\n", tag)
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def clear_chat(self) -> None:
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state=tk.DISABLED)
        self.write_system_status()

    def quick_action(self, command: str) -> None:
        if command.endswith(" "):
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, command)
            self.input_entry.focus_set()
            return
        self.run_command(command)

    def send_command(self) -> None:
        command = self.input_entry.get().strip()
        if not command:
            return
        self.input_entry.delete(0, tk.END)
        self.run_command(command)

    def run_command(self, command: str) -> None:
        if self.processing:
            self.add_message("system", "Jarvis esta ocupado. Espera un momento.")
            return

        self.processing = True
        self.set_busy(True)
        self.add_message("user", f"TU > {command}")

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
            self.root.after(0, lambda: self.add_message(tag, f"JARVIS > {result.message}"))
        except Exception as exc:
            self.root.after(0, lambda: self.add_message("error", f"ERROR > {exc}"))
        finally:
            self.root.after(0, lambda: self.set_busy(False))
            self.processing = False

    def set_busy(self, busy: bool) -> None:
        self.processing = busy
        self.busy_label.config(
            text="EJECUTANDO" if busy else "LISTO",
            fg=self.colors["amber"] if busy else self.colors["green"],
        )
        self.send_btn.config(state=tk.DISABLED if busy else tk.NORMAL)

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
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.add_message("system", "Modo voz iniciado en segundo plano. Pulsa Voz otra vez para detenerlo.")
        except Exception as exc:
            messagebox.showerror("Modo voz", f"No pude iniciar el modo voz:\n{exc}")

    def open_config(self) -> None:
        choice = simpledialog.askstring(
            "Config / PowerShell",
            "Escribe una accion:\n"
            "- config: abrir config.json\n"
            "- memoria: abrir memory.json\n"
            "- ps <comando>: ejecutar PowerShell",
            parent=self.root,
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
            os.startfile(path)  # type: ignore[attr-defined]
            self.add_message("system", f"Abriendo {path.name}.")
        except Exception as exc:
            messagebox.showerror("Abrir archivo", f"No pude abrir {path}:\n{exc}")

    def on_close(self) -> None:
        if self.voice_process and self.voice_process.poll() is None:
            self.voice_process.terminate()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = JarvisGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
