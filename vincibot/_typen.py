"""Erlaubte Texte für die Befehle, als `Literal`-Typen.

Dadurch erkennt der Editor (Linter) Tippfehler sofort, zum Beispiel `roboter.gefuehl("froelich")`.
Ein Test (`tests/test_typen.py`) prüft, dass diese Listen zu den Wörterbüchern passen.
"""
from typing import Literal

Farbname = Literal["rot", "gruen", "grün", "blau", "gelb", "orange", "lila", "tuerkis", "türkis",
                   "rosa", "weiss", "weiß", "schwarz", "aus"]
Farbe = Farbname | tuple[int, int, int]

Position = Literal["links oben", "links mitte", "links unten",
                   "rechts oben", "rechts mitte", "rechts unten"]

Gefuehl = Literal["froehlich", "fröhlich", "wuetend", "wütend", "traurig", "ueberrascht",
                  "überrascht", "aengstlich", "ängstlich", "angeekelt", "begeistert", "schwindelig",
                  "muede", "müde", "schlaefrig", "schläfrig", "wach", "stolz"]
Tanz = Literal["tango", "walzer", "steppen", "samba", "polonaise", "jazz", "rock", "polka",
               "rumba", "disco", "mazurka"]
Bewegung = Literal["umschauen", "verletzt", "sprinten", "kreisen", "schuetteln", "schütteln",
                   "frech", "stolz"]
Geraeusch = Literal["krankenwagen", "polizei", "feuerwehr", "zug", "zugpfeife", "schiffshorn",
                    "flugzeug", "auto", "automotor", "magnetbahn"]
Lied = Literal["funkel", "jingle bells", "geburtstag", "freude", "holzsoldaten", "jagdpolka",
               "elise", "forelle", "peter und der wolf"]
Instrument = Literal["klavier", "e-klavier", "orgel", "gitarre", "e-gitarre", "bass", "zupfbass",
                     "cello", "posaune", "klarinette", "saxophon", "floete", "holzfloete", "fagott",
                     "chor", "vibraphon", "spieluhr", "steeldrum", "marimba", "synthesizer",
                     "weicher synthesizer"]
Note = Literal["c", "d", "e", "f", "g", "a", "h"]

FahrRichtung = Literal["vorwaerts", "vorwärts", "rueckwaerts", "rückwärts", "links", "rechts"]
Rad = Literal["links", "rechts", "beide"]
Einheit = Literal["grad", "umdrehungen", "sekunden"]
Drehrichtung = Literal["uhrzeigersinn", "gegen"]
DisplayRichtung = Literal["hoch", "runter", "links", "rechts"]

Seite = Literal["links", "rechts"]
SensorFarbe = Literal["weiss", "weiß", "rot", "gelb", "gruen", "grün", "blau", "lila", "schwarz"]
Linienfarbe = Literal["schwarz", "weiss", "weiß"]
Farbkanal = Literal["rot", "gruen", "grün", "blau"]
Bodensensor = Literal[1, 2, 3, 4, 5]
Taste = Literal["dreieck", "quadrat", "kreis"]
Fernbedienungstaste = Literal["volume", "mode", "speed", "forward", "backward", "left", "right",
                              "play", "dance", "led", "music", "1", "2", "3"]
