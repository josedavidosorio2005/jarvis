# Subir Jarvis a GitHub

## Prerrequisitos

1. **Git instalado** - Descarga desde: https://git-scm.com
2. **Token de GitHub** - Crea uno en:
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Selecciona permisos: `repo`, `workflow`

## Pasos para subir

### 1. Configurar Git (una vez)
```powershell
git config --global user.name "TuNombre"
git config --global user.email "tu@email.com"
```

### 2. Ejecutar este script
```powershell
.\subir_github.ps1
```

### 3. Ingresa cuando se te pida:
- Tu usuario de GitHub
- Tu token personal
- El nombre del repositorio (ej: jarvis)

---

## Comandos manual (si prefieres)

```powershell
# Inicializar git (ya hecho)
git init

# Agregar archivos
git add .

# Crear commit
git commit -m "Primer commit - Jarvis local con Ollama"

# Crear repositorio en GitHub (usando API)
$token = "TU_TOKEN"
$repo = "jarvis"
Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers @{Authorization="token $token"} -Body (@{name=$repo; description="Asistente local para Windows"; auto_init=$true} | ConvertTo-Json) -ContentType "application/json"

# Agregar remoto
git remote add origin https://github.com/TU_USUARIO/jarvis.git

# Subir
git push -u origin main
```

## Archivos que se subirán

- `jarvis.py` - Asistente principal
- `gui.py` - Interfaz gráfica
- `requirements.txt` - Dependencias
- `README.md` - Documentación
- `install.ps1` - Script de instalación
- `run.ps1` - Script de ejecución
- `setup_*.ps1` - Scripts de configuración
- `config.example.json` - Configuración de ejemplo
- `plugins/` - Plugins del asistente
- `test_*.ps1` - Scripts de prueba

## Archivos ignorados (no se suben)

- `.venv/` - Entorno virtual
- `memory.json` - Memoria local
- `config.json` - Tu configuración personal
- `logs/` - Archivos de log
- `screenshots/` - Capturas de pantalla