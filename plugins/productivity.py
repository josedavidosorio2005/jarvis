from __future__ import annotations

import re
import webbrowser


def register(jarvis):
    jarvis.add_command(r"^abre whatsapp$", open_whatsapp)
    jarvis.add_command(r"^abre gmail$", open_gmail)
    jarvis.add_command(r"^abre calendario$", open_calendar)
    jarvis.add_command(r"^abre spotify$", open_spotify)


def open_whatsapp(_: re.Match):
    from jarvis import ActionResult

    webbrowser.open("https://web.whatsapp.com")
    return ActionResult(True, "Abriendo WhatsApp Web.")


def open_gmail(_: re.Match):
    from jarvis import ActionResult

    webbrowser.open("https://mail.google.com")
    return ActionResult(True, "Abriendo Gmail.")


def open_calendar(_: re.Match):
    from jarvis import ActionResult

    webbrowser.open("https://calendar.google.com")
    return ActionResult(True, "Abriendo Google Calendar.")


def open_spotify(_: re.Match):
    from jarvis import ActionResult

    webbrowser.open("https://open.spotify.com")
    return ActionResult(True, "Abriendo Spotify.")
