from __future__ import annotations

import argparse
import base64
import datetime as dt
import importlib.util
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency fallback
    psutil = None

try:
    import pyautogui
except Exception:  # pragma: no cover - optional dependency fallback
    pyautogui = None

try:
    import pyperclip
except Exception:  # pragma: no cover - optional dependency fallback
    pyperclip = None

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover - optional dependency fallback
    gw = None

try:
    import requests
except Exception:  # pragma: no cover - optional dependency fallback
    requests = None


ROOT = Path(__file__).resolve().parent
SCREENSHOT_DIR = ROOT / "screenshots"
MEMORY_FILE = ROOT / "memory.json"
CONFIG_FILE = ROOT / "config.json"
PLUGINS_DIR = ROOT / "plugins"
LOG_DIR = ROOT / "logs"


APP_ALIASES = {
    "bloc de notas": "notepad",
    "notepad": "notepad",
    "calculadora": "calc",
    "paint": "mspaint",
    "explorador": "explorer",
    "terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "chrome": "chrome",
    "edge": "msedge",
    "word": "winword",
    "excel": "excel",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "calendario": "https://calendar.google.com",
    "spotify": "https://open.spotify.com",
}


@dataclass
class ActionResult:
    ok: bool
    message: str


class MemoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, Any] = {"facts": [], "tasks": [], "favorites": {}, "routines": {}}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            self.data.update(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=True, indent=2), encoding="utf-8")

    def remember(self, text: str) -> None:
        item = {"text": text, "created_at": dt.datetime.now().isoformat(timespec="seconds")}
        self.data.setdefault("facts", []).append(item)
        self.save()

    def add_task(self, text: str) -> None:
        item = {"text": text, "done": False, "created_at": dt.datetime.now().isoformat(timespec="seconds")}
        self.data.setdefault("tasks", []).append(item)
        self.save()

    def summary(self) -> str:
        facts = [item["text"] for item in self.data.get("facts", [])[-10:]]
        tasks = [item["text"] for item in self.data.get("tasks", []) if not item.get("done")]
        if not facts and not tasks:
            return "No tengo memoria guardada todavía."
        lines = []
        if facts:
            lines.append("Recuerdos: " + "; ".join(facts))
        if tasks:
            lines.append("Tareas pendientes: " + "; ".join(tasks[-10:]))
        return "\n".join(lines)


@dataclass
class SimpleTextResponse:
    output_text: str


class OpenAIPlanner:
    def __init__(self, model: str, fallback_provider: str = "ollama", ollama_url: str = "http://localhost:11434", ollama_model: str = "deepseek-r1:8b") -> None:
        self.model = os.environ.get("OPENAI_MODEL", model)
        self.fallback_provider = fallback_provider
        self.ollama_url = os.environ.get("OLLAMA_URL", ollama_url).rstrip("/")
        self.ollama_model = os.environ.get("OLLAMA_MODEL", ollama_model)

    @property
    def available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY")) or self.ollama_available()

    def _client(self):
        from openai import OpenAI

        return OpenAI()

    def create_response(self, **kwargs: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                return self._client().chat.completions.create(**kwargs)
            except Exception as exc:
                last_error = exc
                text = str(exc).lower()
                if not should_fallback_to_ollama(exc) and "rate limit" not in text and "429" not in text:
                    raise
                if self.should_use_ollama_fallback(exc):
                    return self.ollama_response_from_openai_kwargs(**kwargs)
                time.sleep(20 + attempt * 10)
        if self.should_use_ollama_fallback(last_error):
            return self.ollama_response_from_openai_kwargs(**kwargs)
        if last_error is not None:
            raise last_error
        raise RuntimeError("No se pudo llamar a OpenAI.")

    def should_use_ollama_fallback(self, exc: Exception | None = None) -> bool:
        if self.fallback_provider.lower() != "ollama":
            return False
        if exc is None and os.environ.get("OPENAI_API_KEY"):
            return False
        if exc is not None and not should_fallback_to_ollama(exc):
            return False
        return self.ollama_available()

    def ollama_available(self) -> bool:
        if self.fallback_provider.lower() != "ollama" or requests is None:
            return False
        try:
            response = requests.get(self.ollama_url, timeout=2)
            return response.status_code < 500
        except Exception:
            return False

    def ollama_chat(self, messages: list[dict[str, str]], expect_json: bool = False) -> str:
        if requests is None:
            raise RuntimeError("Falta requests. Ejecuta .\\install.ps1.")
        payload: dict[str, Any] = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1},
        }
        if expect_json:
            payload["format"] = "json"
        response = requests.post(f"{self.ollama_url}/api/chat", json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()
        return str(data.get("message", {}).get("content", "")).strip()

    def ollama_response_from_openai_kwargs(self, **kwargs: Any) -> Any:
        input_data = kwargs.get("messages", kwargs.get("input", []))
        messages, expect_json = openai_input_to_ollama_messages(input_data)
        text = self.ollama_chat(messages, expect_json=expect_json)
        return SimpleTextResponse(text)

    def plan(self, user_text: str, memory: MemoryStore, screen_text: str | None = None) -> list[str]:
        if not self.available:
            return []
        prompt = {
            "role": "developer",
            "content": (
                "Eres el cerebro de un asistente local de Windows llamado Jarvis. "
                "Convierte la orden del usuario en una lista JSON de comandos concretos que Jarvis ya entiende. "
                "No inventes capacidades. Si el usuario hace una pregunta general o conversacional, tu unico comando debe ser 'decir <respuesta natural y concisa>'. "
                "Comandos: abre <app/url>, busca <texto>, escribe <texto>, presiona <tecla>, atajo <teclas>, "
                "clic, doble clic, clic derecho, mueve mouse <x> <y>, captura pantalla, mira pantalla, "
                "ventana activa, maximiza ventana, minimiza ventana, cerrar ventana, cambiar ventana, "
                "recuerda que <dato>, tarea <texto>, ejecuta powershell <comando>, ejecuta python <codigo>. "
                "ATENCION MODO DIOS: Si el usuario te pide una tarea compleja que no puedes hacer con comandos simples (ej. crear carpetas, analizar archivos, conectarte a internet, hacer resumenes), DEBES escribir un script en Python y usar el comando 'ejecuta python <codigo>' para resolver el problema de forma autónoma. "
                "La memoria y la pantalla son solo contexto: no las repitas como comandos, "
                "no agregues recuerdos ni tareas salvo que la orden actual lo pida claramente. "
                "Responde solo JSON como: {\"commands\":[\"...\"]}."
            ),
        }
        context = f"Memoria:\n{memory.summary()}"
        if screen_text:
            context += f"\nPantalla:\n{screen_text}"
        response = self.create_response(
            model=self.model,
            messages=[
                prompt,
                {"role": "user", "content": context + "\n\nOrden: " + user_text},
            ],
        )
        text = getattr(response, "output_text", "").strip()
        data = json.loads(extract_json(text))
        return [str(command) for command in data.get("commands", [])]

    def next_step(self, goal: str, memory: MemoryStore, history: list[str], screen: str) -> dict[str, Any]:
        if not self.available:
            return {"status": "blocked", "message": "Necesito OPENAI_API_KEY para modo autonomo."}
        response = self.create_response(
            model=self.model,
            messages=[
                {
                    "role": "developer",
                    "content": (
                        "Eres el planificador autonomo de Jarvis en Windows. "
                        "Completa la meta paso a paso usando solo un comando por turno. "
                        "Usa la pantalla observada y el historial para decidir el siguiente paso. "
                        "Si la meta ya esta cumplida, responde status done. "
                        "Si necesitas contrasenas, codigos, captcha, pagos, borrar datos, enviar mensajes/correos, "
                        "comprar, publicar o hacer algo irreversible, responde status needs_user. "
                        "Comandos permitidos: abre <app/url>, busca <texto>, escribe <texto>, pega texto <texto>, "
                        "presiona <tecla>, atajo <teclas>, clic, clic en <x> <y>, doble clic, clic derecho, "
                        "mueve mouse <x> <y>, espera <segundos>, captura pantalla, mira pantalla, "
                        "ventana activa, maximiza ventana, minimiza ventana, cambiar ventana, decir <texto>, "
                        "ejecuta powershell <comando>, ejecuta python <codigo>. "
                        "ATENCION MODO DIOS: Puedes escribir codigo en Python o Powershell para lograr objetivos complejos que tus herramientas basicas no logren. "
                        "Responde solo JSON: "
                        "{\"status\":\"continue|done|needs_user|blocked\",\"command\":\"...\",\"message\":\"...\"}."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Meta: {goal}\n\n"
                        f"Memoria:\n{memory.summary()}\n\n"
                        f"Historial:\n{chr(10).join(history[-20:]) or 'Sin pasos previos.'}\n\n"
                        f"Pantalla:\n{screen}"
                    ),
                },
            ],
        )
        text = getattr(response, "output_text", "").strip()
        return json.loads(extract_json(text))

    def next_step_from_image(
        self,
        goal: str,
        memory: MemoryStore,
        history: list[str],
        image_path: Path,
        active_window: str,
    ) -> dict[str, Any]:
        if not self.available:
            return {"status": "blocked", "message": "Necesito OPENAI_API_KEY para modo autonomo."}
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        response = self.create_response(
            model=self.model,
            input=[
                {
                    "role": "developer",
                    "content": (
                        "Eres el planificador autonomo de Jarvis en Windows. "
                        "Mira la captura y completa la meta paso a paso usando solo un comando por turno. "
                        "Prefiere comandos directos: usa 'abre bloc de notas' en vez de abrir Inicio y buscar. "
                        "Usa 'busca <texto>' para busquedas web en vez de navegar manualmente. "
                        "Si la meta ya esta cumplida, responde status done. "
                        "Si necesitas contrasenas, codigos, captcha, pagos, borrar datos, enviar mensajes/correos, "
                        "comprar, publicar o hacer algo irreversible, responde status needs_user. "
                        "Comandos permitidos: abre <app/url>, busca <texto>, escribe <texto>, pega texto <texto>, "
                        "presiona <tecla>, atajo <teclas>, clic, clic en <x> <y>, doble clic, clic derecho, "
                        "mueve mouse <dx> <dy> solo para movimiento relativo, espera <segundos>, captura pantalla, mira pantalla, "
                        "ventana activa, maximiza ventana, minimiza ventana, cambiar ventana, decir <texto>, "
                        "ejecuta powershell <comando>. "
                        "Responde solo JSON: "
                        "{\"status\":\"continue|done|needs_user|blocked\",\"command\":\"...\",\"message\":\"...\"}."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"Meta: {goal}\n\n"
                                f"Ventana activa: {active_window}\n\n"
                                f"Memoria:\n{memory.summary()}\n\n"
                                f"Historial:\n{chr(10).join(history[-20:]) or 'Sin pasos previos.'}"
                            ),
                        },
                        {"type": "input_image", "image_url": f"data:image/png;base64,{encoded}"},
                    ],
                },
            ],
        )
        text = getattr(response, "output_text", "").strip()
        return json.loads(extract_json(text))

    def describe_screen(self, image_path: Path, user_text: str) -> str:
        if not self.available:
            return "Puedo capturar la pantalla, pero para entenderla necesito OPENAI_API_KEY."
        if not os.environ.get("OPENAI_API_KEY"):
            return "Ollama local esta disponible para texto, pero la vision de pantalla necesita OpenAI API."
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        response = self.create_response(
            model=self.model,
            messages=[
                {
                    "role": "developer",
                    "content": "Describe la pantalla de Windows con foco en botones, texto visible, errores y acciones posibles. Responde en español breve.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user_text},
                        {"type": "input_image", "image_url": f"data:image/png;base64,{encoded}"},
                    ],
                },
            ],
        )
        return getattr(response, "output_text", "").strip() or "No pude interpretar la pantalla."


class Jarvis:
    def __init__(self, speak: bool = True, auto_confirm: bool = False) -> None:
        self.speak_enabled = speak
        self.auto_confirm = auto_confirm
        self.running = True
        self.config = load_config()
        LOG_DIR.mkdir(exist_ok=True)
        self.memory = MemoryStore(MEMORY_FILE)
        self.ai = OpenAIPlanner(
            self.config.get("openai_model", "gpt-5.4-mini"),
            self.config.get("fallback_provider", "ollama"),
            self.config.get("ollama_url", "http://localhost:11434"),
            self.config.get("ollama_model", "deepseek-r1:8b"),
        )
        self.handlers: list[tuple[re.Pattern[str], Callable[[re.Match[str]], ActionResult]]] = [
            (re.compile(r"^(salir|terminar|apagar jarvis|cerrar jarvis)$", re.I), self.stop),
            (re.compile(r"^(ayuda|comandos)$", re.I), self.help),
            (re.compile(r"^(hora|que hora es)$", re.I), self.tell_time),
            (re.compile(r"^(fecha|que fecha es)$", re.I), self.tell_date),
            (re.compile(r"^abre? (.+)$", re.I), self.open_target),
            (re.compile(r"^busca(?: en internet| en google)? (.+)$", re.I), self.search_web),
            (re.compile(r"^escribe (.+)$", re.I), self.type_text),
            (re.compile(r"^presiona (.+)$", re.I), self.press_key),
            (re.compile(r"^atajo (.+)$", re.I), self.hotkey),
            (re.compile(r"^clic(?: izquierdo)?$", re.I), self.click),
            (re.compile(r"^clic en (-?\d+) (-?\d+)$", re.I), self.click_at),
            (re.compile(r"^doble clic$", re.I), self.double_click),
            (re.compile(r"^clic derecho$", re.I), self.right_click),
            (re.compile(r"^mueve mouse (-?\d+) (-?\d+)$", re.I), self.move_mouse),
            (re.compile(r"^captura pantalla$", re.I), self.screenshot),
            (re.compile(r"^(mira|lee|analiza) pantalla(?: (.+))?$", re.I), self.look_screen),
            (re.compile(r"^ventana activa$", re.I), self.active_window),
            (re.compile(r"^maximiza ventana$", re.I), self.maximize_window),
            (re.compile(r"^minimiza ventana$", re.I), self.minimize_window),
            (re.compile(r"^cerrar ventana$", re.I), self.close_window),
            (re.compile(r"^cambiar ventana$", re.I), self.switch_window),
            (re.compile(r"^pega portapapeles$", re.I), self.paste_clipboard),
            (re.compile(r"^pega texto (.+)$", re.I), self.paste_text),
            (re.compile(r"^copia (.+)$", re.I), self.copy_text),
            (re.compile(r"^recuerda que (.+)$", re.I), self.remember),
            (re.compile(r"^(que recuerdas|memoria)$", re.I), self.recall),
            (re.compile(r"^tarea (.+)$", re.I), self.add_task),
            (re.compile(r"^planifica (.+)$", re.I), self.plan_and_run),
            (re.compile(r"^(haz|autonomo|modo autonomo) (.+)$", re.I), self.autonomous),
            (re.compile(r"^decir (.+)$", re.I), self.say),
            (re.compile(r"^lista procesos$", re.I), self.list_processes),
            (re.compile(r"^ejecuta powershell (.+)$", re.I), self.run_powershell),
            (re.compile(r"^espera (\d+)$", re.I), self.wait),
        ]
        self.load_plugins()

    def add_command(self, pattern: str, handler: Callable[[re.Match[str]], ActionResult]) -> None:
        self.handlers.insert(0, (re.compile(pattern, re.I), handler))

    def load_plugins(self) -> None:
        if not PLUGINS_DIR.exists():
            return
        for path in PLUGINS_DIR.glob("*.py"):
            if path.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            register = getattr(module, "register", None)
            if callable(register):
                register(self)

    def speak(self, text: str) -> None:
        print(f"Jarvis: {text}")
        if not self.speak_enabled:
            return
        
        def run_tts():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 160)
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass
                
        import threading
        threading.Thread(target=run_tts, daemon=True).start()

    def execute(self, raw_command: str) -> ActionResult:
        command = normalize(raw_command)
        if not command:
            return ActionResult(False, "No entendí el comando.")

        for pattern, handler in self.handlers:
            match = pattern.match(command)
            if match:
                try:
                    return handler(match)
                except Exception as exc:
                    return ActionResult(False, f"Falló la acción: {exc}")

        if self.ai.available:
            return self.run_ai_plan(raw_command)
        return ActionResult(False, f"No tengo ese comando todavía: {raw_command}. Si configuras OPENAI_API_KEY puedo interpretar frases libres.")

    def stop(self, _: re.Match[str]) -> ActionResult:
        self.running = False
        return ActionResult(True, "Cerrando Jarvis.")

    def help(self, _: re.Match[str]) -> ActionResult:
        commands = [
            "abre calculadora",
            "abre https://openai.com",
            "busca automatizacion rpa windows",
            "escribe hola mundo",
            "presiona enter",
            "atajo ctrl l",
            "clic / doble clic / clic derecho",
            "clic en 500 300",
            "mueve mouse 100 0",
            "captura pantalla",
            "mira pantalla",
            "ventana activa / maximiza ventana / minimiza ventana / cerrar ventana / cambiar ventana",
            "recuerda que mi nombre es ...",
            "que recuerdas",
            "tarea llamar a ...",
            "planifica abre Gmail y busca ...",
            "haz abre Gmail y busca ...",
            "copia texto para el portapapeles",
            "pega texto hola mundo",
            "pega portapapeles",
            "lista procesos",
            "ejecuta powershell Get-Process | Select-Object -First 5",
            "salir",
        ]
        return ActionResult(True, "Comandos disponibles:\n  - " + "\n  - ".join(commands))

    def tell_time(self, _: re.Match[str]) -> ActionResult:
        return ActionResult(True, "Son las " + dt.datetime.now().strftime("%H:%M"))

    def tell_date(self, _: re.Match[str]) -> ActionResult:
        return ActionResult(True, "Hoy es " + dt.datetime.now().strftime("%Y-%m-%d"))

    def open_target(self, match: re.Match[str]) -> ActionResult:
        target = match.group(1).strip()
        lower = target.lower()

        if lower in APP_ALIASES:
            alias_target = APP_ALIASES[lower]
            if alias_target.startswith("http"):
                webbrowser.open(alias_target)
            else:
                subprocess.Popen([alias_target], shell=True)
            return ActionResult(True, f"Abriendo {target}.")

        if looks_like_url(target):
            webbrowser.open(ensure_url(target))
            return ActionResult(True, f"Abriendo {target}.")

        path = Path(os.path.expandvars(os.path.expanduser(target.strip('"'))))
        if path.exists():
            os.startfile(path)  # type: ignore[attr-defined]
            return ActionResult(True, f"Abriendo {path}.")

        found_lnk = find_windows_executable(target)
        if found_lnk:
            os.startfile(found_lnk)
            return ActionResult(True, f"Encontré y abrí {target}.")

        subprocess.Popen(target, shell=True)
        return ActionResult(True, f"Intentando abrir {target}.")

    def search_web(self, match: re.Match[str]) -> ActionResult:
        query = match.group(1).strip()
        webbrowser.open("https://www.google.com/search?q=" + quote_plus(query))
        return ActionResult(True, f"Buscando {query}.")

    def type_text(self, match: re.Match[str]) -> ActionResult:
        require_pyautogui()
        text = match.group(1)
        pyautogui.write(text, interval=0.01)
        return ActionResult(True, "Texto escrito.")

    def press_key(self, match: re.Match[str]) -> ActionResult:
        require_pyautogui()
        key = normalize_key(match.group(1))
        pyautogui.press(key)
        return ActionResult(True, f"Presioné {key}.")

    def hotkey(self, match: re.Match[str]) -> ActionResult:
        require_pyautogui()
        keys = [normalize_key(k) for k in re.split(r"[+\s]+", match.group(1)) if k.strip()]
        pyautogui.hotkey(*keys)
        return ActionResult(True, "Atajo ejecutado: " + " + ".join(keys))

    def click(self, _: re.Match[str]) -> ActionResult:
        require_pyautogui()
        pyautogui.click()
        return ActionResult(True, "Clic.")

    def click_at(self, match: re.Match[str]) -> ActionResult:
        require_pyautogui()
        x = int(match.group(1))
        y = int(match.group(2))
        pyautogui.click(x=x, y=y)
        return ActionResult(True, f"Clic en {x}, {y}.")

    def double_click(self, _: re.Match[str]) -> ActionResult:
        require_pyautogui()
        pyautogui.doubleClick()
        return ActionResult(True, "Doble clic.")

    def right_click(self, _: re.Match[str]) -> ActionResult:
        require_pyautogui()
        pyautogui.rightClick()
        return ActionResult(True, "Clic derecho.")

    def move_mouse(self, match: re.Match[str]) -> ActionResult:
        require_pyautogui()
        x = int(match.group(1))
        y = int(match.group(2))
        pyautogui.moveRel(x, y, duration=0.2)
        return ActionResult(True, f"Mouse movido {x}, {y}.")

    def screenshot(self, _: re.Match[str]) -> ActionResult:
        filename = self.capture_screen("screenshot")
        return ActionResult(True, f"Captura guardada en {filename}.")

    def look_screen(self, match: re.Match[str]) -> ActionResult:
        filename = self.capture_screen("screen")
        request = match.group(2) or "Dime que ves en la pantalla y que puedo hacer."
        description = self.ai.describe_screen(filename, request)
        return ActionResult(True, description)

    def observe_screen(self, goal: str) -> str:
        filename = self.capture_screen("observe")
        active = self.get_active_window_title()
        description = self.ai.describe_screen(
            filename,
            "Observa esta pantalla para completar la meta. "
            "Incluye texto visible, app activa, botones importantes y coordenadas aproximadas si puedes. "
            f"Meta: {goal}",
        )
        return f"Ventana activa: {active}\nCaptura: {filename}\n{description}"

    def get_active_window_title(self) -> str:
        try:
            if gw is not None and gw.getActiveWindow() is not None:
                return gw.getActiveWindow().title
        except Exception:
            pass
        return "desconocida"

    def capture_screen(self, prefix: str) -> Path:
        require_pyautogui()
        SCREENSHOT_DIR.mkdir(exist_ok=True)
        filename = SCREENSHOT_DIR / f"{prefix}-{dt.datetime.now():%Y%m%d-%H%M%S}.png"
        pyautogui.screenshot(str(filename))
        return filename

    def active_window(self, _: re.Match[str]) -> ActionResult:
        require_windows()
        window = gw.getActiveWindow()
        if window is None:
            return ActionResult(False, "No detecté una ventana activa.")
        return ActionResult(True, f"Ventana activa: {window.title}")

    def maximize_window(self, _: re.Match[str]) -> ActionResult:
        require_windows()
        window = gw.getActiveWindow()
        if window:
            window.maximize()
            return ActionResult(True, "Ventana maximizada.")
        return ActionResult(False, "No detecté una ventana activa.")

    def minimize_window(self, _: re.Match[str]) -> ActionResult:
        require_windows()
        window = gw.getActiveWindow()
        if window:
            window.minimize()
            return ActionResult(True, "Ventana minimizada.")
        return ActionResult(False, "No detecté una ventana activa.")

    def close_window(self, _: re.Match[str]) -> ActionResult:
        if not self.confirm("cerrar la ventana activa"):
            return ActionResult(False, "Cancelado.")
        require_windows()
        window = gw.getActiveWindow()
        if window:
            window.close()
            return ActionResult(True, "Ventana cerrada.")
        return ActionResult(False, "No detecté una ventana activa.")

    def switch_window(self, _: re.Match[str]) -> ActionResult:
        require_pyautogui()
        pyautogui.hotkey("alt", "tab")
        return ActionResult(True, "Cambié de ventana.")

    def copy_text(self, match: re.Match[str]) -> ActionResult:
        if pyperclip is None:
            raise RuntimeError("Falta pyperclip. Ejecuta .\\install.ps1.")
        pyperclip.copy(match.group(1))
        return ActionResult(True, "Texto copiado al portapapeles.")

    def remember(self, match: re.Match[str]) -> ActionResult:
        self.memory.remember(match.group(1))
        return ActionResult(True, "Lo recordare.")

    def recall(self, _: re.Match[str]) -> ActionResult:
        return ActionResult(True, self.memory.summary())

    def add_task(self, match: re.Match[str]) -> ActionResult:
        self.memory.add_task(match.group(1))
        return ActionResult(True, "Tarea guardada.")

    def say(self, match: re.Match[str]) -> ActionResult:
        return ActionResult(True, match.group(1))

    def plan_and_run(self, match: re.Match[str]) -> ActionResult:
        return self.run_ai_plan(match.group(1))

    def autonomous(self, match: re.Match[str]) -> ActionResult:
        goal = match.group(2).strip()
        return self.run_autonomous(goal)

    def paste_clipboard(self, _: re.Match[str]) -> ActionResult:
        require_pyautogui()
        pyautogui.hotkey("ctrl", "v")
        return ActionResult(True, "Pegado.")

    def paste_text(self, match: re.Match[str]) -> ActionResult:
        if pyperclip is None:
            raise RuntimeError("Falta pyperclip. Ejecuta .\\install.ps1.")
        require_pyautogui()
        pyperclip.copy(match.group(1))
        pyautogui.hotkey("ctrl", "v")
        return ActionResult(True, "Texto pegado.")

    def list_processes(self, _: re.Match[str]) -> ActionResult:
        if psutil is None:
            raise RuntimeError("Falta psutil. Ejecuta .\\install.ps1.")
        names = []
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info.get("name")
                if name and name not in names:
                    names.append(name)
            except psutil.Error:
                continue
            if len(names) >= 15:
                break
        return ActionResult(True, "Procesos visibles: " + ", ".join(names))

    def run_powershell(self, match: re.Match[str]) -> ActionResult:
        command = match.group(1)
        if is_dangerous(command) and not self.confirm(f"ejecutar PowerShell peligroso: {command}"):
            return ActionResult(False, "Cancelado.")
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            text=True,
            capture_output=True,
            timeout=60,
        )
        output = (completed.stdout or completed.stderr).strip()
        if len(output) > 1200:
            output = output[:1200] + "\n..."
        return ActionResult(completed.returncode == 0, output or "Comando ejecutado.")

    def wait(self, match: re.Match[str]) -> ActionResult:
        seconds = min(int(match.group(1)), 3600)
        time.sleep(seconds)
        return ActionResult(True, f"Esperé {seconds} segundos.")

    def run_ai_plan(self, raw_command: str) -> ActionResult:
        if not self.ai.available:
            return ActionResult(False, "Para interpretar frases libres necesito OPENAI_API_KEY.")
        try:
            commands = self.ai.plan(raw_command, self.memory)
        except Exception as exc:
            return ActionResult(False, f"No pude generar el plan con IA: {exc}")
        if not commands:
            return ActionResult(False, "La IA no devolvió acciones.")
        messages = [f"Plan: {', '.join(commands)}"]
        for command in commands:
            result = self.execute(command)
            messages.append(result.message)
            if not result.ok:
                break
        return ActionResult(True, "\n".join(messages))

    def run_autonomous(self, goal: str) -> ActionResult:
        local_commands = local_plan(goal)
        if local_commands:
            messages = [f"Plan local: {', '.join(local_commands)}"]
            for command in local_commands:
                result = self.execute(command)
                messages.append(result.message)
                if not result.ok:
                    return ActionResult(False, "\n".join(messages))
                time.sleep(0.8)
            return ActionResult(True, "\n".join(messages))

        if not self.ai.available:
            return ActionResult(False, "Para modo autonomo necesito OPENAI_API_KEY.")
        if can_use_fast_plan(goal):
            fast_result = self.run_ai_plan(goal)
            if fast_result.ok:
                return ActionResult(True, "Tarea ejecutada con plan rapido.\n" + fast_result.message)

        max_steps = int(self.config.get("max_autonomous_steps", 12))
        history: list[str] = []
        log_path = LOG_DIR / f"autonomo-{dt.datetime.now():%Y%m%d-%H%M%S}.log"

        for step in range(1, max_steps + 1):
            try:
                image_path = self.capture_screen("autonomo")
                active_window = self.get_active_window_title()
                decision = self.ai.next_step_from_image(goal, self.memory, history, image_path, active_window)
            except Exception as exc:
                return ActionResult(False, f"Modo autonomo fallo al pensar: {exc}")

            status = str(decision.get("status", "blocked")).lower()
            command = str(decision.get("command", "")).strip()
            message = str(decision.get("message", "")).strip()
            log_line = f"[{step}] status={status} command={command!r} message={message}"
            history.append(log_line)
            append_log(log_path, log_line)

            if status == "done":
                return ActionResult(True, "Tarea terminada.\n" + "\n".join(history))
            if status in {"needs_user", "blocked"}:
                return ActionResult(False, f"Necesito tu ayuda: {message or command}\nLog: {log_path}")
            if not command:
                return ActionResult(False, f"La IA no dio comando en el paso {step}.\nLog: {log_path}")
            if requires_user_confirmation(command) and not self.confirm(f"modo autonomo quiere ejecutar: {command}"):
                return ActionResult(False, "Cancelado por seguridad.")

            result = self.execute(command)
            result_line = f"[{step}] result ok={result.ok} message={result.message}"
            history.append(result_line)
            append_log(log_path, result_line)
            if not result.ok:
                return ActionResult(False, "La tarea se detuvo.\n" + "\n".join(history[-6:]) + f"\nLog: {log_path}")
            time.sleep(float(self.config.get("autonomous_step_delay", 1.0)))

        return ActionResult(False, f"Llegue al limite de {max_steps} pasos. Revisa el log: {log_path}")

    def confirm(self, action: str) -> bool:
        if self.auto_confirm or not self.config.get("require_confirmation", True):
            return True
        answer = input(f"Confirmar {action}? escribe SI: ").strip()
        return answer == "SI"


def normalize(text: str) -> str:
    text = text.strip().lower()
    for prefix in ("jarvis ", "por favor "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text)


def normalize_key(key: str) -> str:
    key = normalize(key)
    for prefix in ("tecla ", "la tecla ", "boton "):
        if key.startswith(prefix):
            key = key[len(prefix) :]
    aliases = {
        "control": "ctrl",
        "intro": "enter",
        "entrar": "enter",
        "escape": "esc",
        "espacio": "space",
        "suprimir": "delete",
        "borrar": "backspace",
        "flecha arriba": "up",
        "flecha abajo": "down",
        "flecha izquierda": "left",
        "flecha derecha": "right",
        "windows": "win",
    }
    return aliases.get(key, key)


def looks_like_url(text: str) -> bool:
    return "." in text and " " not in text or text.startswith(("http://", "https://"))


def ensure_url(text: str) -> str:
    if text.startswith(("http://", "https://")):
        return text
    return "https://" + text


def quote_plus(text: str) -> str:
    from urllib.parse import quote_plus as _quote_plus

    return _quote_plus(text)


def require_pyautogui() -> None:
    if pyautogui is None:
        raise RuntimeError("Falta pyautogui. Ejecuta .\\install.ps1.")


def require_windows() -> None:
    if gw is None:
        raise RuntimeError("Falta pygetwindow. Ejecuta .\\install.ps1.")


def is_dangerous(command: str) -> bool:
    lowered = command.lower()
    dangerous = ["remove-item", " del ", " rmdir", "format ", "shutdown", "stop-computer", "restart-computer", "cipher /w"]
    return any(token in lowered for token in dangerous)


def requires_user_confirmation(command: str) -> bool:
    lowered = normalize(command)
    risky = [
        "cerrar ventana",
        "ejecuta powershell",
        "remove-item",
        "borrar",
        "eliminar",
        "comprar",
        "pagar",
        "enviar",
        "publicar",
        "formatear",
        "shutdown",
        "restart",
    ]
    return any(token in lowered for token in risky)


def can_use_fast_plan(goal: str) -> bool:
    lowered = normalize(goal)
    visual_words = [
        "mira",
        "pantalla",
        "lee",
        "ver",
        "boton",
        "clic",
        "descarga",
        "resultado",
        "correo",
        "gmail",
        "whatsapp",
        "web",
    ]
    return not any(word in lowered for word in visual_words)


def find_windows_executable(app_name: str) -> str | None:
    norm_name = normalize(app_name).replace(" ", "")
    if not norm_name:
        return None
    search_dirs = [
        Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs",
    ]
    for directory in search_dirs:
        if not directory.exists():
            continue
        for lnk_file in directory.rglob("*.lnk"):
            stem_norm = normalize(lnk_file.stem).replace(" ", "")
            if norm_name in stem_norm or stem_norm in norm_name:
                return str(lnk_file)
    return None


def local_plan(goal: str) -> list[str]:
    text = normalize(goal)
    parts = [part.strip() for part in re.split(r"\s+y\s+|\s+luego\s+|\s+despues\s+", text) if part.strip()]
    if not parts:
        return []

    commands: list[str] = []
    known_prefixes = (
        "abre ",
        "busca ",
        "escribe ",
        "pega texto ",
        "presiona ",
        "atajo ",
        "espera ",
        "captura pantalla",
        "mira pantalla",
        "ventana activa",
        "maximiza ventana",
        "minimiza ventana",
        "cambiar ventana",
        "decir ",
    )
    for part in parts:
        if part.startswith(known_prefixes):
            commands.append(part)
            continue
        if commands and commands[-1].startswith(("abre ", "busca ")):
            commands.append("pega texto " + part)
            continue
        return []
    return commands if len(commands) > 1 else []


def append_log(path: Path, text: str) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {text}\n")


def extract_json(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    match = re.search(r"\{.*\}", text, re.S)
    return match.group(0) if match else text


def should_fallback_to_ollama(exc: Exception) -> bool:
    text = str(exc).lower()
    needles = [
        "rate limit",
        "429",
        "quota",
        "insufficient_quota",
        "billing",
        "api key",
        "authentication",
        "connection",
        "timeout",
    ]
    return any(needle in text for needle in needles)


def openai_input_to_ollama_messages(input_items: Any) -> tuple[list[dict[str, str]], bool]:
    if isinstance(input_items, str):
        return [{"role": "user", "content": input_items}], False

    messages: list[dict[str, str]] = []
    expect_json = False
    for item in input_items or []:
        if not isinstance(item, dict):
            continue
        role = item.get("role", "user")
        if role == "developer":
            role = "system"
        content = item.get("content", "")
        text = content_to_text(content)
        if text:
            messages.append({"role": str(role), "content": text})
    return messages or [{"role": "user", "content": ""}], expect_json


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "input_text":
                chunks.append(str(part.get("text", "")))
            elif part.get("type") == "input_image":
                chunks.append("[Imagen omitida: Ollama fallback de texto no procesa esta captura en Jarvis.]")
        return "\n".join(chunk for chunk in chunks if chunk)
    return str(content)


def load_config() -> dict[str, Any]:
    default = {
        "openai_model": "gpt-5.4-mini",
        "assistant_name": "Jarvis",
        "wake_word": "jarvis",
        "require_confirmation": True,
        "max_autonomous_steps": 12,
        "autonomous_step_delay": 1.0,
        "fallback_provider": "ollama",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "deepseek-r1:8b",
    }
    if CONFIG_FILE.exists():
        default.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    return default


def interactive_loop(jarvis: Jarvis) -> None:
    jarvis.speak("Jarvis listo. Escribe ayuda para ver comandos.")
    while jarvis.running:
        try:
            command = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        result = jarvis.execute(command)
        jarvis.speak(result.message)


def voice_loop(jarvis: Jarvis, culture: str, wake_word: str | None) -> None:
    listener = ROOT / "voice_listener_py.py"
    process = subprocess.Popen(
        [sys.executable, str(listener)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    jarvis.speak("Iniciando escucha por voz.")
    assert process.stdout is not None
    listen_next = False
    for line in process.stdout:
        text = line.strip()
        if not text:
            continue
        if text.startswith("__JARVIS_READY__"):
            active_culture = text.replace("__JARVIS_READY__", "") or culture
            jarvis.speak(f"Ya estoy escuchando con reconocimiento {active_culture}.")
            continue
        if text == "__JARVIS_NO_RECOGNIZERS__":
            jarvis.speak(
                "Windows no tiene reconocedores de voz instalados. "
                "Puedes usar el modo texto o instalar un paquete de reconocimiento de voz en Configuración."
            )
            break
        if text == "__JARVIS_MIC_ERROR__":
            jarvis.speak("No pude acceder al micrófono.")
            continue
            
        norm_text = normalize(text)
        if wake_word and wake_word.lower() in norm_text:
            command = norm_text.replace(wake_word.lower(), "", 1).strip()
            if not command:
                jarvis.speak("Sí, dime.")
                listen_next = True
                continue
            listen_next = False
        elif listen_next:
            command = norm_text
            listen_next = False
        elif not wake_word:
            command = norm_text
        else:
            continue
            
        print(f"Tu voz: {command}")
        if not command:
            continue
        result = jarvis.execute(command)
        jarvis.speak(result.message)
        if not jarvis.running:
            process.terminate()
            break


def check_and_start_ollama() -> bool:
    """Verifica si Ollama está instalado y ejecuta los modelos necesarios."""
    import shutil

    # Rutas posibles donde puede estar Ollama
    ollama_paths = [
        "C:\\Users\\Usuario\\AppData\\Local\\Programs\\Ollama\\ollama.exe",
        os.path.expandvars("%LOCALAPPDATA%\\Programs\\Ollama\\ollama.exe"),
    ]

    # Verificar si ollama está en el PATH o en rutas conocidas
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        # Buscar en rutas conocidas
        for path in ollama_paths:
            if os.path.exists(path):
                ollama_path = path
                break

    if not ollama_path:
        print("⚠️ Ollama no está instalado o no está en el PATH.")
        print("   Instala Ollama desde: https://ollama.com")
        return False

    # Asegurar que Ollama esté en el PATH para los comandos siguientes
    ollama_dir = str(Path(ollama_path).parent)
    os.environ["PATH"] = ollama_dir + os.pathsep + os.environ.get("PATH", "")

    # Modelos a iniciar
    ollama_models = [
        "openclaw",
        "claude",
        "codex",
        "opencode",
        "droid",
        "pi"
    ]

    print("🤖 Verificando modelos de Ollama...")
    print("   (Los modelos se descargarán la primera vez que se usen)")

    # Verificar si Ollama está corriendo
    try:
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        available_models = result.stdout.lower() if result.returncode == 0 else ""
    except Exception:
        available_models = ""

    for model in ollama_models:
        if model in available_models:
            print(f"   ✓ {model} disponible")
        else:
            print(f"   ○ {model} (se descargará cuando lo uses)")

    print("   Listo. Ollama está configurado.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Jarvis local para Windows con comandos RPA.")
    parser.add_argument("--voice", action="store_true", help="Escuchar comandos por micrófono usando Windows Speech.")
    parser.add_argument("--silent", action="store_true", help="No hablar por voz, solo imprimir texto.")
    parser.add_argument("--yes", action="store_true", help="Aceptar confirmaciones de acciones delicadas.")
    parser.add_argument("--culture", default="es-ES", help="Cultura de reconocimiento, por ejemplo es-ES o es-MX.")
    parser.add_argument("--wake-word", default=None, help="Palabra de activacion para modo voz. Por defecto usa config.json.")
    parser.add_argument("--no-wake-word", action="store_true", help="Procesar todo lo que escuche en modo voz.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Comando directo, por ejemplo: abre calculadora")
    args = parser.parse_args()

    if platform.system() != "Windows":
        print("Este asistente está pensado para Windows.")

    # Verificar e iniciar Ollama
    check_and_start_ollama()

    jarvis = Jarvis(speak=not args.silent, auto_confirm=args.yes)
    if args.command:
        command = " ".join(args.command)
        if command.startswith("--"):
            command = shlex.join(args.command)
        result = jarvis.execute(command)
        jarvis.speak(result.message)
        return 0 if result.ok else 1

    if args.voice:
        wake_word = None if args.no_wake_word else args.wake_word or jarvis.config.get("wake_word", "jarvis")
        voice_loop(jarvis, args.culture, wake_word)
    else:
        interactive_loop(jarvis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
