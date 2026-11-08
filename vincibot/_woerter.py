"""Internes: Wörterbücher (Deutsch -> Befehle des Roboters) und Hilfsfunktionen."""
from collections.abc import Mapping
from typing import TypeVar

Farbe = str | tuple[int, int, int]
_T = TypeVar("_T")

# ---------------------------------------------------------------- Wörterbücher (Deutsch -> Roboter)
FARBEN: dict[str, tuple[int, int, int]] = {
    "rot": (255, 0, 0), "gruen": (0, 255, 0), "grün": (0, 255, 0), "blau": (0, 0, 255),
    "gelb": (255, 200, 0), "orange": (255, 100, 0), "lila": (160, 0, 255),
    "tuerkis": (0, 220, 220), "türkis": (0, 220, 220), "rosa": (255, 80, 160),
    "weiss": (255, 255, 255), "weiß": (255, 255, 255), "schwarz": (0, 0, 0), "aus": (0, 0, 0),
}
FARBEN_SENSOR: dict[str, str] = {"weiss": "white", "weiß": "white", "rot": "red", "gelb": "yellow",
                 "gruen": "green", "grün": "green", "blau": "blue", "lila": "purple",
                 "schwarz": "black"}
GEFUEHLE: dict[str, str] = {
    "froehlich": "happy", "fröhlich": "happy", "wuetend": "angry", "wütend": "angry",
    "traurig": "sad", "ueberrascht": "surprised", "überrascht": "surprised",
    "aengstlich": "feared", "ängstlich": "feared", "angeekelt": "disgusted",
    "begeistert": "joyful", "schwindelig": "dizzy", "muede": "fatigued", "müde": "fatigued",
    "schlaefrig": "sleepy", "schläfrig": "sleepy", "wach": "awake", "stolz": "proud",
}
TAENZE: dict[str, str] = {"tango": "tango", "walzer": "waltz", "steppen": "tap", "samba": "samba",
          "polonaise": "polonaise", "jazz": "jazz", "rock": "rock", "polka": "polka",
          "rumba": "rumba", "disco": "disco", "mazurka": "mazurka"}
BEWEGUNGEN: dict[str, str] = {"umschauen": "look around", "verletzt": "hurt", "sprinten": "sprint",
              "kreisen": "circling", "schuetteln": "shake", "schütteln": "shake",
              "frech": "naughty", "stolz": "proud"}
GERAEUSCHE: dict[str, str] = {
    "krankenwagen": "ambulance", "polizei": "police car", "feuerwehr": "fire engine",
    "zug": "train", "zugpfeife": "train whistle", "schiffshorn": "boat whistle",
    "flugzeug": "aircraft", "auto": "automobile", "automotor": "automobile engine",
    "magnetbahn": "magnetically levitated train",
}
LIEDER: dict[str, str] = {
    "funkel": "twinkle", "jingle bells": "jingle bells", "geburtstag": "happy birthday to you",
    "freude": "ode to joy", "holzsoldaten": "parade of the wooden soldiers",
    "jagdpolka": "hunting polka", "elise": "to alice", "forelle": "die forelle",
    "peter und der wolf": "peter and the wolf",
}
INSTRUMENTE: list[str] = ["klavier", "e-klavier", "orgel", "gitarre", "e-gitarre", "bass", "zupfbass",
               "cello", "posaune", "klarinette", "saxophon", "floete", "holzfloete", "fagott",
               "chor", "vibraphon", "spieluhr", "steeldrum", "marimba", "synthesizer",
               "weicher synthesizer"]
# Tonhöhen in Hertz für die vierte Oktave (deutsche Notennamen: h statt b/si)
NOTEN: dict[str, int] = {"c": 262, "d": 294, "e": 330, "f": 349, "g": 392, "a": 440, "h": 494}


class RoboterFehler(Exception):
    """Etwas ist beim Steuern des Roboters schiefgegangen."""


def farbe_umrechnen(farbe: Farbe) -> tuple[int, int, int]:
    """Nimmt einen Farbnamen ('rot') oder drei Zahlen (255, 0, 0) und gibt (r, g, b) zurück."""
    if isinstance(farbe, str):
        name = farbe.lower().strip()
        if name not in FARBEN:
            raise RoboterFehler(f"Die Farbe '{farbe}' kenne ich nicht. Mögliche Farben: "
                                + ", ".join(sorted({k for k in FARBEN if k.isascii()})))
        return FARBEN[name]
    r, g, b = farbe
    for wert in (r, g, b):
        if not 0 <= wert <= 255:
            raise RoboterFehler("Farbwerte müssen zwischen 0 und 255 liegen.")
    return (int(r), int(g), int(b))


def waehle(name: object, tabelle: Mapping[str, _T], art: str) -> _T:
    schluessel = str(name).lower().strip()
    if schluessel not in tabelle:
        raise RoboterFehler(f"Ich kenne {art} '{name}' nicht. Mögliche Werte: "
                            + ", ".join(sorted({k for k in tabelle if k.isascii()})))
    return tabelle[schluessel]


