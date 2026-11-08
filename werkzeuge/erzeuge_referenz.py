"""Erzeugt docs/referenz.md aus den Beschreibungen im Code.  Aufruf: python werkzeuge/erzeuge_referenz.py"""
import inspect
import pathlib

from vincibot import VinciBotAsync

ABSCHNITTE = [
    ("Fahren", ["vorwaerts", "rueckwaerts", "links", "rechts", "fahre", "stoppe", "raeder",
                "strecke_mit_tempo", "drehe_mit_tempo", "rad_drehen", "rad_stopp",
                "raddurchmesser", "radabstand", "fahr_einstellungen_zuruecksetzen"]),
    ("Lichter (die 6 bunten LEDs)", ["licht", "licht_einzeln", "lichter", "licht_aus"]),
    ("Display vorne", ["schreibe", "zeige_bild", "zeige_bild_fuer", "zeige_pixel",
                       "display_helligkeit", "display_richtung", "display_drehen", "display_aus"]),
    ("Gefühle, Tänze, Bewegungen", ["gefuehl", "tanze", "bewege_dich"]),
    ("Töne und Musik", ["geraeusch", "lied", "sprich", "ton", "pause", "instrument", "tempo",
                        "aktuelles_tempo", "trommel", "spiele_datei", "lautstaerke",
                        "lautstaerke_aendern", "ton_stopp"]),
    ("Sensoren", ["abstand", "helligkeit", "untergrund", "lautstaerke_umgebung", "sieht_farbe",
                  "farbwert", "hindernis_naeher_als", "linie_erkannt", "sensorwerte",
                  "farbsensor_kalibrieren"]),
    ("Infrarot", ["sende_infrarot", "empfange_infrarot", "infrarot_angekommen", "fernbedienung"]),
    ("Warten", ["warte", "warte_bis", "sensorstrom"]),
    ("Für Fortgeschrittene", ["roh"]),
]

zeilen = ["# Alle Befehle auf einen Blick", "",
          "*Diese Datei wird automatisch aus dem Code erzeugt (`python werkzeuge/erzeuge_referenz.py`).*",
          "*In `VinciBotAsync` (async) heißen alle Befehle gleich, man schreibt nur `await` davor.*", ""]
benutzt = set()
for titel, namen in ABSCHNITTE:
    zeilen += [f"## {titel}", ""]
    for name in namen:
        funktion = getattr(VinciBotAsync, name)
        benutzt.add(name)
        kopf = str(inspect.signature(funktion)).replace("(self, ", "(").replace("(self)", "()")
        beschreibung = inspect.cleandoc(funktion.__doc__ or "")
        zeilen += [f"### `{name}{kopf}`", "", beschreibung, ""]
vergessen = [n for n, f in inspect.getmembers(VinciBotAsync, inspect.iscoroutinefunction)
             if not n.startswith("_") and n not in benutzt and n not in ("verbinden", "trennen")]
assert not vergessen, f"Nicht in der Referenz: {vergessen}"
pathlib.Path(__file__).resolve().parent.parent.joinpath("docs", "referenz.md").write_text(
    "\n".join(zeilen), encoding="utf-8")
print("docs/referenz.md geschrieben")
