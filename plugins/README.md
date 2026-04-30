# Plugins de Jarvis

Pon aquí archivos `.py` con una función:

```python
def register(jarvis):
    jarvis.add_command(r"^mi comando$", mi_funcion)
```

La función recibe un `re.Match` y devuelve `ActionResult`.
