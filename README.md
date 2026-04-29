# Jarvis para Windows

Asistente local estilo Jarvis para automatizar Windows con comandos en español. Tiene modo texto, voz con el motor de reconocimiento de Windows, voz de respuesta, apertura de apps, búsqueda web, control de teclado/mouse, capturas y comandos PowerShell.

La IA conversacional se activa con una API key de OpenAI. No usa directamente tu cuenta de ChatGPT: necesita `OPENAI_API_KEY`. Si OpenAI falla por limite, cuota o clave, Jarvis puede usar Ollama local como respaldo con DeepSeek.

## Instalación

Abre PowerShell en esta carpeta y ejecuta:

```powershell
.\install.ps1
```

## Uso

Modo texto:

```powershell
.\run.ps1
```

Modo voz:

```powershell
.\run.ps1 --voice
```

Por defecto el modo voz espera la palabra de activación `jarvis`. Para escuchar todo:

```powershell
.\run.ps1 --voice --no-wake-word
```

Comando directo:

```powershell
.\run.ps1 abre calculadora
.\run.ps1 busca inteligencia artificial para windows
```

## Activar IA conversacional

Guarda tu API key de OpenAI para Windows:

```powershell
.\setup_openai_key.ps1 sk-tu-clave
```

Cierra y vuelve a abrir PowerShell. Luego puedes usar frases libres:

```powershell
.\run.ps1 "abre gmail y busca el correo de Juan"
.\run.ps1 "recuerda que mi app favorita para notas es bloc de notas"
.\run.ps1 "mira la pantalla y dime que error aparece"
```

Modo autonomo supervisado:

```powershell
.\run.ps1 "haz abre bloc de notas y escribe una nota corta"
.\run.ps1 "autonomo busca clima en Google y dime el resultado"
```

En modo autonomo Jarvis mira la pantalla, decide un paso, lo ejecuta, vuelve a mirar y repite hasta terminar. Si detecta contrasenas, pagos, borrar datos, enviar mensajes/correos, publicar o algo irreversible, se detiene y pide ayuda.

El modelo por defecto está en `config.example.json`. Si quieres cambiarlo, copia ese archivo como `config.json` y edítalo. La documentación actual de OpenAI recomienda los modelos GPT-5.4 para trabajo agentico; `gpt-5.4-mini` queda como opción más barata y rápida.

## Respaldo local con Ollama

Instala Ollama para Windows desde:

```text
https://ollama.com/download/windows
```

Luego cierra y abre PowerShell, y ejecuta:

```powershell
.\setup_ollama.ps1
.\test_ollama.ps1
```

Jarvis queda configurado para usar:

```json
{
  "fallback_provider": "ollama",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "deepseek-r1:8b"
}
```

Ollama sirve como cerebro local de texto. La vision de pantalla sigue usando OpenAI cuando esta disponible.

## Comandos incluidos

- `ayuda`
- `hora`
- `fecha`
- `abre calculadora`
- `abre bloc de notas`
- `abre https://openai.com`
- `busca automatizacion rpa windows`
- `escribe hola mundo`
- `presiona enter`
- `atajo ctrl l`
- `clic`
- `clic en 500 300`
- `doble clic`
- `clic derecho`
- `mueve mouse 100 0`
- `captura pantalla`
- `mira pantalla`
- `ventana activa`
- `maximiza ventana`
- `minimiza ventana`
- `cerrar ventana`
- `cambiar ventana`
- `recuerda que mi nombre es ...`
- `que recuerdas`
- `tarea comprar ...`
- `planifica abre Gmail y busca ...`
- `haz abre Gmail y busca ...`
- `copia texto para el portapapeles`
- `pega texto hola mundo`
- `pega portapapeles`
- `lista procesos`
- `ejecuta powershell Get-Process | Select-Object -First 5`
- `salir`

## Seguridad

Jarvis pide confirmación antes de cerrar ventanas o ejecutar comandos PowerShell peligrosos. Para automatizaciones controladas puedes pasar `--yes`, pero úsalo con cuidado:

```powershell
.\run.ps1 --yes ejecuta powershell Get-Process
```

El modo autonomo guarda registros en `logs/` para revisar que hizo paso a paso. Puedes ajustar sus limites en `config.json`:

```json
{
  "max_autonomous_steps": 12,
  "autonomous_step_delay": 1.0
}
```

## Plugins

Los plugins viven en `plugins/`. Ya hay uno de productividad con:

- `abre whatsapp`
- `abre gmail`
- `abre calendario`
- `abre spotify`

## Notas importantes

Este Jarvis puede controlar mouse, teclado y ejecutar PowerShell. Eso es poderoso y también delicado. Úsalo con comandos claros y prueba primero en ventanas sin información importante.

El modo voz usa `System.Speech` de Windows. Jarvis intenta usar `es-ES`, luego cualquier reconocedor de español y, si no existe, el primer reconocedor instalado. Para ver los reconocedores disponibles:

```powershell
Add-Type -AssemblyName System.Speech
[System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | ForEach-Object { $_.Culture.Name }
```

Si la lista sale vacía, instala un paquete de reconocimiento de voz desde Configuración de Windows o usa el modo texto con `.\run.ps1`.

## Cómo ampliarlo

Los comandos están en `jarvis.py`, dentro de la lista `self.handlers`. Para agregar una acción nueva:

1. Crea una expresión regular para el comando.
2. Crea un método que devuelva `ActionResult`.
3. Añádelo a `self.handlers`.
