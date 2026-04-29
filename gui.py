"""
Interfaz gráfica para Jarvis - Asistente Local
"""
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import subprocess
import sys
import os
from pathlib import Path

# Agregar el directorio actual al path para importar jarvis
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Intentar importar el módulo jarvis
try:
    from jarvis import Jarvis
    JARVIS_AVAILABLE = True
except ImportError as e:
    JARVIS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Jarvis - Asistente Local")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e2e")

        # Colores
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.user_color = "#f38ba8"
        self.jarvis_color = "#a6e3a1"

        self.setup_ui()
        self.jarvis = None
        self.processing = False

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Título
        title_label = tk.Label(
            self.root,
            text="🤖 Jarvis - Asistente Local",
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        )
        title_label.pack(pady=10)

        # Frame del chat
        chat_frame = tk.Frame(self.root, bg=self.bg_color)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Área de texto del chat
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            font=("Segoe UI", 11),
            bg="#313244",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)

        # Configurar tags de color
        self.chat_area.tag_config("user", foreground=self.user_color, lmargin1=10, lmargin2=10)
        self.chat_area.tag_config("jarvis", foreground=self.jarvis_color, lmargin1=10, lmargin2=10)
        self.chat_area.tag_config("system", foreground="#9399b2", font=("Segoe UI", 9, "italic"))

        # Frame de entrada
        input_frame = tk.Frame(self.root, bg=self.bg_color)
        input_frame.pack(fill=tk.X, padx=20, pady=10)

        # Campo de texto
        self.input_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 12),
            bg="#313244",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self.send_command())

        # Botón enviar
        send_btn = tk.Button(
            input_frame,
            text="Enviar",
            font=("Segoe UI", 11),
            bg=self.accent_color,
            fg=self.bg_color,
            command=self.send_command,
            relief=tk.FLAT,
            padx=20,
            pady=5
        )
        send_btn.pack(side=tk.RIGHT)

        # Botón voz
        voice_btn = tk.Button(
            input_frame,
            text="🎤 Voz",
            font=("Segoe UI", 11),
            bg="#45475a",
            fg=self.fg_color,
            command=self.toggle_voice,
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        voice_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Mensaje inicial
        self.add_message("system", "💡 Escribe un comando y presiona Enter o haz clic en Enviar.")
        self.add_message("system", "📌 Comandos de ejemplo: 'abre calculadora', 'qué hora es', 'ayuda'")

        # Verificar estado de Jarvis
        if not JARVIS_AVAILABLE:
            self.add_message("system", f"⚠️ Advertencia: {IMPORT_ERROR}")
        else:
            self.add_message("system", "✅ Módulo Jarvis cargado correctamente")

    def add_message(self, tag, message):
        """Agrega un mensaje al chat"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + "\n\n", tag)
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def send_command(self):
        """Envía el comando escrito"""
        if self.processing:
            return

        command = self.input_entry.get().strip()
        if not command:
            return

        # Mostrar comando del usuario
        self.add_message("user", f"Tu: {command}")
        self.input_entry.delete(0, tk.END)

        # Procesar en hilo separado
        self.processing = True
        thread = threading.Thread(target=self.process_command, args=(command,))
        thread.daemon = True
        thread.start()

    def process_command(self, command):
        """Procesa el comando en un hilo separado"""
        try:
            if not JARVIS_AVAILABLE:
                self.root.after(0, lambda: self.add_message("jarvis", 
                    "⚠️ No se pudo importar jarvis.py. Verifica que esté en la misma carpeta."))
                return

            # Crear instancia de Jarvis si no existe
            if self.jarvis is None:
                self.jarvis = Jarvis(speak=False, auto_confirm=True)

            # Ejecutar comando
            result = self.jarvis.execute(command)

            # Mostrar respuesta
            self.root.after(0, lambda: self.add_message("jarvis", f"Jarvis: {result.message}"))

        except Exception as e:
            self.root.after(0, lambda: self.add_message("jarvis", f"❌ Error: {str(e)}"))
        finally:
            self.processing = False

    def toggle_voice(self):
        """Activa/desactiva el modo voz"""
        messagebox.showinfo("🎤 Modo Voz", 
            "Para usar reconocimiento de voz, ejecuta:\npython jarvis.py --voice\n\nDesde la terminal.")


def main():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()