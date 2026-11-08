# pyright: reportAny=false, reportExplicitAny=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false
# pyright: reportUnknownLambdaType=false, reportImplicitStringConcatenation=false
"""Konverter zwischen Scratch-Projekten (MatataCode `.mc`, Scratch `.sb3`) und Python.

    python -m vincibot.scratch projekt.mc            # erzeugt projekt.py
    python -m vincibot.scratch programm.py           # erzeugt programm.mc

Aus Scratch wird ein Python-Programm mit der einfachen Klasse `VinciBot`. Umgekehrt werden einfache
Python-Programme (Befehle, Schleifen, if/else, Variablen, Rechnen) zu Scratch-Blöcken.
Was nicht umgewandelt werden kann, erscheint als Warnung, nie stillschweigend.
"""
from __future__ import annotations

import ast
import hashlib
import json
import keyword
import re
import sys
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._woerter import (BEWEGUNGEN, FARBEN, FARBEN_SENSOR, GEFUEHLE, GERAEUSCHE, INSTRUMENTE,
                       LIEDER, POSITION_NAMEN, TAENZE)

__all__ = ["Ergebnis", "UmwandlungsFehler", "scratch_zu_python", "python_zu_scratch",
           "scratch_datei_zu_python", "python_datei_zu_scratch"]


class UmwandlungsFehler(Exception):
    """Die Datei konnte nicht umgewandelt werden."""


@dataclass
class Ergebnis:
    """Ergebnis einer Umwandlung: der erzeugte Inhalt und alle Warnungen."""
    inhalt: Any
    warnungen: list[str] = field(default_factory=list)


def _umkehr(tabelle: dict[str, str]) -> dict[str, str]:
    """Englisch -> Deutsch (bevorzugt Schreibweise ohne Umlaute)."""
    ergebnis: dict[str, str] = {}
    for deutsch, englisch in sorted(tabelle.items(), key=lambda p: (not p[0].isascii(), p[0])):
        _ = ergebnis.setdefault(englisch, deutsch)
    return ergebnis


EN_GEFUEHL = _umkehr(GEFUEHLE)
EN_TANZ = _umkehr(TAENZE)
EN_BEWEGUNG = _umkehr(BEWEGUNGEN)
EN_GERAEUSCH = _umkehr(GERAEUSCHE)
EN_LIED = _umkehr(LIEDER)
EN_FARBE_SENSOR = _umkehr(FARBEN_SENSOR)
TASTEN = {"triangle": "dreieck", "square": "quadrat", "circular": "kreis"}
TASTEN_UMGEKEHRT = {v: k for k, v in TASTEN.items()}
RICHTUNG_FAHRE = {"forward": "vorwaerts", "backward": "rueckwaerts", "left": "links",
                  "right": "rechts"}
RICHTUNG_DISPLAY = {"up": "hoch", "down": "runter", "left": "links", "right": "rechts"}
RAEDER = {"L": "links", "R": "rechts", "L+R": "beide"}
EINHEITEN = {"degrees": "grad", "rotations": "umdrehungen", "seconds": "sekunden"}
DREHRICHTUNG = {"clockwise": "uhrzeigersinn", "counterclockwise": "gegen"}

# Hat-Blöcke, die das Programm starten
START_HUETE = {"matatacarEvents_whenRobotStart", "event_whenflagclicked"}

# Vorlagen für Befehlsblöcke ohne eigene deutsche Methode: werden als `roboter.roh(...)` ausgegeben
VORLAGEN: dict[str, str] = {
    "matatacarMotion_startMoving2": 'motion.start_moving("[DIRECTION]", [SPEED])',
    "matatacarMotor_motionSetMotorSpeed": 'motion.motor_pwm("[WHEEL]", [SPEED])',
    "matatacarLight_setRgbLedPanel": "leds.display([PANEL])",
    "matatacarSensors_resetTimer": "timer.reset_timer()",
}


# ============================================================================================
#  Scratch  ->  Python
# ============================================================================================
def _python_name(name: str) -> str:
    sauber = re.sub(r"\W", "_", name.strip()).strip("_") or "variable"
    if sauber[0].isdigit():
        sauber = "v_" + sauber
    if keyword.iskeyword(sauber) or sauber in ("roboter", "random", "VinciBot"):
        sauber += "_"
    return sauber


def _zahl_oder_text(text: object) -> str:
    wert = str(text).strip()
    if wert == "":
        return "0"
    try:
        return repr(int(wert))
    except ValueError:
        pass
    try:
        gleitkomma = float(wert)
        return repr(gleitkomma) if gleitkomma == gleitkomma and abs(gleitkomma) != float("inf") \
            else repr(wert)
    except ValueError:
        return repr(wert)


def _einruecken(zeilen: list[str]) -> list[str]:
    return ["    " + z if z else z for z in zeilen]


def _hex_zu_tupel(farbe: str) -> str | None:
    treffer = re.fullmatch(r"#?([0-9a-fA-F]{6})", farbe.strip())
    if not treffer:
        return None
    wert = treffer.group(1)
    return f"({int(wert[0:2], 16)}, {int(wert[2:4], 16)}, {int(wert[4:6], 16)})"


class _ZuPython:
    def __init__(self, ziele: list[dict[str, Any]]) -> None:
        self.ziele: list[dict[str, Any]] = ziele
        self.warnungen: list[str] = []
        self.variablen: dict[str, str] = {}      # Scratch-ID -> Python-Name
        self.beschreibung: str = ""
        self.benutzt: set[str] = set()
        self.zugewiesen: set[str] = set()         # in der aktuellen Funktion zugewiesene Variablen
        self.blocke: dict[str, Any] = {}
        for ziel in ziele:
            for vid, daten in ziel.get("variables", {}).items():
                self.variablen[vid] = _python_name(str(daten[0]))

    # ------------------------------------------------------------------ Hilfen
    def warne(self, text: str) -> None:
        if text not in self.warnungen:
            self.warnungen.append(text)

    def feld(self, block: dict[str, Any], name: str) -> str:
        wert = block.get("fields", {}).get(name)
        return str(wert[0]) if wert else ""

    def menu(self, block: dict[str, Any], name: str) -> str | None:
        """Wert eines Auswahlfeldes (Menü), falls die Eingabe ein einfaches Menü ist."""
        eingabe = block.get("inputs", {}).get(name)
        if not eingabe or not isinstance(eingabe[1], str):
            return None
        menue = self.blocke.get(eingabe[1])
        if not menue:
            return None
        if "_menu_" in menue["opcode"] or menue["opcode"] in _KONSTANTEN:
            felder = menue.get("fields", {})
            return str(next(iter(felder.values()))[0]) if felder else None
        if menue["opcode"] in _LISTEN_REPORTER:
            return self.feld(menue, _LISTEN_REPORTER[menue["opcode"]])
        return None

    def wert(self, block: dict[str, Any], name: str, standard: str = "0") -> str:
        eingabe = block.get("inputs", {}).get(name)
        if not eingabe or len(eingabe) < 2 or eingabe[1] is None:
            return standard
        return self._wert(eingabe[1])

    def _wert(self, inhalt: Any) -> str:
        if isinstance(inhalt, list):
            art = inhalt[0]
            if art in (4, 5, 6, 7, 8):
                return _zahl_oder_text(inhalt[1])
            if art == 12:
                return self.variablen.get(str(inhalt[2]), _python_name(str(inhalt[1])))
            return repr(str(inhalt[1]))
        if isinstance(inhalt, str):
            return self.ausdruck(inhalt)
        return "None"

    def zeichenkette(self, block: dict[str, Any], name: str) -> str:
        """Wie `wert`, aber immer als Text."""
        menue = self.menu(block, name)
        if menue is not None:
            return repr(menue)
        ausdruck = self.wert(block, name, "''")
        return ausdruck if ausdruck.startswith(("'", '"')) else f"str({ausdruck})"

    def bedingung(self, block: dict[str, Any], name: str = "CONDITION") -> str:
        eingabe = block.get("inputs", {}).get(name)
        if not eingabe or len(eingabe) < 2 or not isinstance(eingabe[1], str):
            return "False"
        return self.ausdruck(eingabe[1])

    # ------------------------------------------------------------------ Ausdrücke
    def ausdruck(self, bid: str) -> str:
        b = self.blocke.get(bid)
        if b is None:
            return "None"
        op = b["opcode"]
        if "_menu_" in op or op in _KONSTANTEN or op in _LISTEN_REPORTER:
            felder = b.get("fields", {})
            wert = self.menu_wert_direkt(b)
            return _zahl_oder_text(wert) if op in _KONSTANTEN and op != "faceLed" else repr(wert) \
                if felder else "None"
        if op == "data_variable":
            vid = b["fields"]["VARIABLE"][1]
            return self.variablen.get(str(vid), _python_name(str(b["fields"]["VARIABLE"][0])))
        binaer = {"operator_add": "+", "operator_subtract": "-", "operator_multiply": "*",
                  "operator_divide": "/", "operator_mod": "%"}
        if op in binaer:
            return f"({self.wert(b, 'NUM1')} {binaer[op]} {self.wert(b, 'NUM2')})"
        vergleich = {"operator_lt": "<", "operator_gt": ">", "operator_equals": "=="}
        if op in vergleich:
            return f"({self.wert(b, 'OPERAND1')} {vergleich[op]} {self.wert(b, 'OPERAND2')})"
        if op == "operator_and":
            return f"({self.bedingung(b, 'OPERAND1')} and {self.bedingung(b, 'OPERAND2')})"
        if op == "operator_or":
            return f"({self.bedingung(b, 'OPERAND1')} or {self.bedingung(b, 'OPERAND2')})"
        if op == "operator_not":
            return f"(not {self.bedingung(b, 'OPERAND')})"
        if op == "operator_round":
            return f"round({self.wert(b, 'NUM')})"
        if op == "operator_random":
            self.benutzt.add("random")
            return f"random.randint({self.wert(b, 'FROM')}, {self.wert(b, 'TO')})"
        if op == "operator_join":
            return f"(str({self.wert(b, 'STRING1', repr(''))}) + str({self.wert(b, 'STRING2', repr(''))}))"
        if op == "operator_length":
            return f"len(str({self.wert(b, 'STRING', repr(''))}))"
        if op == "operator_mathop":
            funktion = self.feld(b, "OPERATOR")
            if funktion == "abs":
                return f"abs({self.wert(b, 'NUM')})"
            if funktion in ("floor", "ceiling", "sqrt"):
                self.benutzt.add("math")
                name = {"floor": "floor", "ceiling": "ceil", "sqrt": "sqrt"}[funktion]
                return f"math.{name}({self.wert(b, 'NUM')})"
            self.warne(f"Rechenfunktion '{funktion}' wird nicht unterstützt.")
            return "0"
        sensoren = {
            "matatacarSensors_getObstacleDistance": "roboter.abstand()",
            "matatacarSensors_loudness": "roboter.lautstaerke_umgebung()",
            "matatacarSound_getVolume": "roboter.lautstaerke()",
            "matatacarMusic_getTempo": "roboter.aktuelles_tempo()",
            "matatacarSensors_getMessage": "roboter.empfange_infrarot()",
        }
        if op in sensoren:
            return sensoren[op]
        if op == "matatacarSensors_getRGBColor":
            farbe = {"red": "rot", "green": "gruen", "blue": "blau"}.get(
                self.menu(b, "COLOR_CHANNEL") or "", "rot")
            return f"roboter.farbwert({farbe!r})"
        if op == "matatacarSensors_getAmbientLight":
            seite = {"left": "links", "right": "rechts"}.get(self.menu(b, "LIGHT_POSTION") or "", "links")
            return f"roboter.helligkeit({seite!r})"
        if op == "matatacarSensors_isObstaclesAhead":
            nahe = f"roboter.hindernis_naeher_als({self.wert(b, 'VALUE')})"
            return nahe if self.menu(b, "COMPARE") == "<" else f"(not {nahe})"
        if op == "matatacarSensors_recognizeColor":
            englisch = self.menu(b, "COLOR_TYPE") or ""
            deutsch = EN_FARBE_SENSOR.get(englisch)
            if deutsch is None:
                self.warne(f"Farbe '{englisch}' (Farbsensor) ist unbekannt.")
                return "False"
            return f"roboter.sieht_farbe({deutsch!r})"
        if op == "matatacarSensors_isButtonPressed":
            taste = self.menu(b, "BUTTON_KEY") or ""
            if taste in TASTEN:
                return f"roboter.taste_gedrueckt({TASTEN[taste]!r})"
            self.warne(f"Taste '{taste}' kennt der VinciBot nicht.")
            return "False"
        if op == "matatacarSensors_waitIRMessage":
            return f"roboter.infrarot_angekommen(str({self.wert(b, 'MESSAGE_INDEX')}))"
        self.warne(f"Block '{op}' wird nicht unterstützt (Wert wird durch 0 ersetzt).")
        return "0"

    @staticmethod
    def menu_wert_direkt(block: dict[str, Any]) -> str:
        felder = block.get("fields", {})
        return str(next(iter(felder.values()))[0]) if felder else ""

    # ------------------------------------------------------------------ Anweisungen
    def kette(self, start: str | None) -> list[str]:
        zeilen: list[str] = []
        bid = start
        while bid:
            b = self.blocke.get(bid)
            if b is None:
                break
            zeilen += self.anweisung(b)
            bid = b.get("next")
        return zeilen or ["pass"]

    def unterstapel(self, block: dict[str, Any], name: str = "SUBSTACK") -> list[str]:
        eingabe = block.get("inputs", {}).get(name)
        if not eingabe or len(eingabe) < 2 or not isinstance(eingabe[1], str):
            return ["pass"]
        return self.kette(eingabe[1])

    def roh(self, vorlage: str, block: dict[str, Any]) -> str:
        """`roboter.roh(...)` aus einer Vorlage mit [PLATZHALTERN]."""
        teile = re.split(r"\[([A-Z_0-9]+)\]", vorlage)
        ausdruecke: list[str] = []
        for i, teil in enumerate(teile):
            if i % 2 == 0:
                if teil:
                    ausdruecke.append(repr(teil))
            else:
                menue = self.menu(block, teil)
                ausdruecke.append(repr(menue) if menue is not None else f"str({self.wert(block, teil)})")
        zusammen = " + ".join(ausdruecke)
        zusammen = re.sub(r"'\s*\+\s*'", "", zusammen)
        return f"roboter.roh({zusammen})"

    def anweisung(self, b: dict[str, Any]) -> list[str]:
        op = b["opcode"]
        # ---- Steuerung, Variablen
        if op == "control_wait":
            return [f"roboter.warte({self.wert(b, 'DURATION')})"]
        if op == "control_repeat":
            anzahl = self.wert(b, "TIMES")
            anzahl = anzahl if re.fullmatch(r"\d+", anzahl) else f"int({anzahl})"
            return [f"for _ in range({anzahl}):"] + _einruecken(self.unterstapel(b))
        if op == "control_forever":
            return ["while True:"] + _einruecken(self.unterstapel(b))
        if op == "control_if":
            return [f"if {self.bedingung(b)}:"] + _einruecken(self.unterstapel(b))
        if op == "control_if_else":
            return ([f"if {self.bedingung(b)}:"] + _einruecken(self.unterstapel(b)) + ["else:"]
                    + _einruecken(self.unterstapel(b, "SUBSTACK2")))
        if op == "control_repeat_until":
            return [f"while not {self.bedingung(b)}:"] + _einruecken(self.unterstapel(b))
        if op == "control_wait_until":
            return [f"while not {self.bedingung(b)}:", "    roboter.warte(0.05)"]
        if op == "control_stop":
            return ["raise SystemExit" if self.feld(b, "STOP_OPTION") != "this script" else "return"]
        if op in ("data_setvariableto", "data_changevariableby"):
            vid = str(b["fields"]["VARIABLE"][1])
            name = self.variablen.get(vid, _python_name(str(b["fields"]["VARIABLE"][0])))
            self.zugewiesen.add(name)
            operator = "=" if op == "data_setvariableto" else "+="
            return [f"{name} {operator} {self.wert(b, 'VALUE')}"]
        if op in ("data_showvariable", "data_hidevariable"):
            return []
        # ---- Fahren
        if op in ("matatacarMotion_movePosition",):
            richtung = self.menu(b, "DIRECTION") or "forward"
            einheit = self.menu(b, "POS_UNIT") or "cm"
            wert = self.wert(b, "VALUE")
            if einheit in ("cm", "inch"):
                strecke = wert if einheit == "cm" else f"{wert} * 2.54"
                return [f"roboter.{'vorwaerts' if richtung == 'forward' else 'rueckwaerts'}({strecke})"]
            return [self.roh_mit(f'motion.move_position("{richtung}", [VALUE], "{einheit}")', b)]
        if op == "matatacarMotion_moveAngle":
            richtung = self.menu(b, "DIRECTION") or "left"
            einheit = self.menu(b, "ANGLE_UNIT") or "degrees"
            wert = self.wert(b, "VALUE")
            if einheit in ("degrees", "rotations"):
                winkel = wert if einheit == "degrees" else f"{wert} * 360"
                return [f"roboter.{'links' if richtung == 'left' else 'rechts'}({winkel})"]
            return [self.roh_mit(f'motion.move_angle("{richtung}", [VALUE], "{einheit}")', b)]
        if op in ("matatacarMotion_startMoving", "matatacarMotion_startMoving2"):
            richtung = RICHTUNG_FAHRE.get(self.menu(b, "DIRECTION") or "forward", "vorwaerts")
            return [f"roboter.fahre({richtung!r}, {self.wert(b, 'SPEED', '50')})"]
        if op == "matatacarMotion_motionStopMoving":
            return ["roboter.stoppe()"]
        if op in ("matatacarMotion_movePositionSpeed", "matatacarMotion_movePositionSpeedUntilDone"):
            vorzeichen = "-" if self.menu(b, "DIRECTION") == "backward" else ""
            faktor = {"cm": "10", "inch": "25.4"}.get(self.menu(b, "POS_UNIT") or "cm", "10")
            warten = op.endswith("UntilDone")
            return [f"roboter.strecke_mit_tempo({vorzeichen}{self.wert(b, 'VALUE')} * {faktor}, "
                    f"{self.wert(b, 'SPEED', '50')}, {warten})"]
        if op in ("matatacarMotion_moveAngleSpeed", "matatacarMotion_moveAngleSpeedUntilDone"):
            vorzeichen = "-" if self.menu(b, "DIRECTION") == "right" else ""
            faktor = " * 360" if self.menu(b, "ANGLE_UNIT") == "rotations" else ""
            warten = op.endswith("UntilDone")
            return [f"roboter.drehe_mit_tempo({vorzeichen}{self.wert(b, 'VALUE')}{faktor}, "
                    f"{self.wert(b, 'SPEED', '50')}, {warten})"]
        if op == "matatacarMotor_motionMotorRun":
            return [self.rad_lauf(b, mit_tempo=False)]
        if op == "matatacarMotor_motionMotorRunWithSpeed":
            return [self.rad_lauf(b, mit_tempo=True)]
        if op == "matatacarMotor_motionStopMotor":
            rad = RAEDER.get(self.menu(b, "WHEEL") or "L+R", "beide")
            return [f"roboter.rad_stopp({rad!r})"]
        # ---- Gefühle, Tänze
        if op == "matatacarPerformance_doEmotion":
            return [self.benannt(b, "EMOTION_INDEX", EN_GEFUEHL, "gefuehl", "action.emotion")]
        if op == "matatacarPerformance_doDance":
            return [self.benannt(b, "DANCE_INDEX", EN_TANZ, "tanze", "action.dance")]
        if op == "matatacarPerformance_doAction":
            return [self.benannt(b, "ACTION_INDEX", EN_BEWEGUNG, "bewege_dich", "action.behavior")]
        # ---- Display
        if op == "matatacarLight_displayWriteText":
            return [f"roboter.schreibe({self.zeichenkette(b, 'TEXT')})"]
        if op in ("matatacarLight_displayShowImage", "matatacarLight_displayShowImageWithTime"):
            bild = self.bild(b)
            if op.endswith("WithTime"):
                return [f"roboter.zeige_bild_fuer({bild}, {self.wert(b, 'TIME', '2')})"]
            return [f"roboter.zeige_bild({bild})"]
        if op == "matatacarLight_displayTurnOff":
            return ["roboter.display_aus()"]
        if op == "matatacarLight_displaySetBrightness":
            return [f"roboter.display_helligkeit({self.wert(b, 'BRIGHTNESS', '100')})"]
        if op == "matatacarLight_displaySetPixel":
            return [f"roboter.zeige_pixel({self.wert(b, 'X_AXIS')}, {self.wert(b, 'Y_AXIS')}, "
                    f"{self.wert(b, 'BRIGHTNESS', '100')})"]
        if op == "matatacarLight_displayScreenRotate":
            richtung = DREHRICHTUNG.get(self.menu(b, "ROTATE") or "clockwise", "uhrzeigersinn")
            return [f"roboter.display_drehen({richtung!r})"]
        if op == "matatacarLight_displaySetOrientation":
            richtung = RICHTUNG_DISPLAY.get(self.menu(b, "ORIENTATION") or "up", "hoch")
            return [f"roboter.display_richtung({richtung!r})"]
        # ---- Lichter
        if op == "matatacarLight_rgbLedAllSet":
            return [f"roboter.licht({self.farbe(b)})"]
        if op == "matatacarLight_rgbLedSingleSet":
            return [f"roboter.licht_einzeln({self.position(b)}, {self.farbe(b)})"]
        if op == "matatacarLight_rgbLedAllSet1":
            return [f"roboter.licht(({self.wert(b, 'RED_VALUE')}, {self.wert(b, 'GREEN_VALUE')}, "
                    f"{self.wert(b, 'BLUE_VALUE')}))"]
        if op == "matatacarLight_rgbLedSingleSet1":
            return [f"roboter.licht_einzeln({self.position(b)}, ({self.wert(b, 'RED_VALUE')}, "
                    f"{self.wert(b, 'GREEN_VALUE')}, {self.wert(b, 'BLUE_VALUE')}))"]
        if op == "matatacarLight_rgbLedAllOff":
            return ["roboter.licht_aus()"]
        # ---- Ton
        if op in ("matatacarSound_doEffect", "matatacarSound_doEffectUntilDone"):
            warten = op.endswith("UntilDone")
            return [self.benannt(b, "EFFECT", EN_GERAEUSCH, "geraeusch", "audio.effect", warten)]
        if op in ("matatacarSound_doSing", "matatacarSound_singUntilDone"):
            warten = op.endswith("UntilDone")
            return [self.benannt(b, "SONG", EN_LIED, "lied", "audio.sing", warten)]
        if op in ("matatacarSound_say", "matatacarSound_sayUntilDone"):
            return [f"roboter.sprich({self.zeichenkette(b, 'MESSAGE')}, {op.endswith('UntilDone')})"]
        if op in ("matatacarSound_audioPlay", "matatacarSound_audioPlayUntilDone"):
            return [f"roboter.spiele_datei({self.zeichenkette(b, 'PATH')}, {op.endswith('UntilDone')})"]
        if op in ("matatacarMusic_playNoteForBeats", "music_playNoteForBeats"):
            return [f"roboter.ton_hoehe({self.wert(b, 'NOTE', '60')}, {self.wert(b, 'BEATS', '0.25')})"]
        if op in ("matatacarMusic_restForBeats", "music_restForBeats"):
            return [f"roboter.pause({self.wert(b, 'BEATS', '0.25')})"]
        if op in ("matatacarMusic_setTempo", "music_setTempo"):
            return [f"roboter.tempo({self.wert(b, 'TEMPO', '60')})"]
        if op in ("matatacarMusic_changeTempo", "music_changeTempo"):
            return [f"roboter.tempo_aendern({self.wert(b, 'TEMPO', '20')})"]
        if op in ("matatacarMusic_setInstrument", "music_setInstrument"):
            nummer = self.menu(b, "INSTRUMENT") or self.wert(b, "INSTRUMENT", "1")
            try:
                return [f"roboter.instrument({INSTRUMENTE[int(str(nummer).strip(chr(39))) - 1]!r})"]
            except (ValueError, IndexError):
                self.warne(f"Instrument '{nummer}' ist unbekannt.")
                return []
        if op == "matatacarSensors_sendIRMessage":
            return [f"roboter.sende_infrarot(str({self.wert(b, 'MESSAGE_INDEX')}))"]
        if op == "matatacarSensors_resetTimer":
            self.warne("Der Scratch-Zeitgeber wird nicht umgewandelt.")
            return []
        if op in VORLAGEN:
            return [self.roh(VORLAGEN[op], b)]
        self.warne(f"Block '{op}' wird nicht unterstützt und übersprungen.")
        return [f"# Nicht unterstützt: {op}"]

    # ------------------------------------------------------------------ Teilstücke
    def roh_mit(self, vorlage: str, block: dict[str, Any]) -> str:
        return self.roh(vorlage, block)

    def benannt(self, b: dict[str, Any], eingabe: str, tabelle: dict[str, str], methode: str,
                roh_befehl: str, warten: bool | None = None) -> str:
        """Methode mit einem deutschen Namen; unbekannte Werte gehen über `roh`."""
        englisch = self.menu(b, eingabe)
        zusatz = "" if warten is None else f", {warten}"
        if englisch is None:
            self.warne(f"Eingabe {eingabe} ist keine feste Auswahl; es wird 'roh' verwendet.")
            wert = self.wert(b, eingabe, "''")
            return f"roboter.roh({roh_befehl!r} + '(' + repr(str({wert})){zusatz and ' + ' + repr(zusatz)} + ')')"
        if englisch in tabelle:
            return f"roboter.{methode}({tabelle[englisch]!r}{zusatz})"
        self.warne(f"'{englisch}' hat keinen deutschen Namen; es wird 'roh' verwendet.")
        return f"roboter.roh({roh_befehl + '(' + repr(englisch) + zusatz + ')'!r})"

    def position(self, b: dict[str, Any]) -> str:
        """Nummer des Lichts (1-6) als Positionsname."""
        wert = self.wert(b, "LED_INDEX", "1")
        if re.fullmatch(r"\d+", wert) and int(wert) in POSITION_NAMEN:
            return repr(POSITION_NAMEN[int(wert)])
        self.warne(f"Die Nummer des Lichts ({wert}) muss eine feste Zahl von 1 bis 6 sein; es wird 'links oben' verwendet.")
        return "'links oben'"

    def farbe(self, b: dict[str, Any]) -> str:
        eingabe = b.get("inputs", {}).get("COLOR")
        if eingabe and isinstance(eingabe[1], list) and eingabe[1][0] == 9:
            tupel = _hex_zu_tupel(str(eingabe[1][1]))
            if tupel:
                return tupel
        self.warne("Eine Farbe war kein fester Farbwert; es wird Weiß verwendet.")
        return "(255, 255, 255)"

    def bild(self, b: dict[str, Any]) -> str:
        bits = self.menu(b, "PANEL") or ""
        if not re.fullmatch(r"[01]{128}", bits):
            self.warne("Ein Display-Bild konnte nicht gelesen werden; es bleibt leer.")
            bits = "0" * 128
        zeilen = [bits[i * 16:(i + 1) * 16].replace("1", "#").replace("0", ".") for i in range(8)]
        return "[" + ", ".join(repr(z) for z in zeilen) + "]"

    def rad_lauf(self, b: dict[str, Any], mit_tempo: bool) -> str:
        rad = RAEDER.get(self.menu(b, "WHEEL") or "L+R", "beide")
        einheit = EINHEITEN.get(self.menu(b, "ANGLE_UNIT") or "degrees", "grad")
        richtung = DREHRICHTUNG.get(self.menu(b, "ROTATE") or "clockwise", "uhrzeigersinn")
        tempo = self.wert(b, "SPEED", "100") if mit_tempo else "100"
        return (f"roboter.rad_drehen({rad!r}, {self.wert(b, 'VALUE')}, {einheit!r}, {tempo}, "
                f"{richtung!r})")

    # ------------------------------------------------------------------ Gesamtes Programm
    def erzeuge(self, name: str) -> str:
        skripte: list[tuple[str, dict[str, Any], str]] = []   # (ziel, hat, id)
        for ziel in self.ziele:
            self.blocke = ziel.get("blocks", {})
            alle = {k: v for k, v in self.blocke.items() if isinstance(v, dict)}
            self.blocke = alle
            oben = sorted((k for k, v in alle.items() if v.get("topLevel") and not v.get("shadow")),
                          key=lambda k: (alle[k].get("y", 0), alle[k].get("x", 0)))
            for k in oben:
                skripte.append((ziel["name"], alle, k))
        if not skripte:
            self.warne("Das Projekt enthält keine Skripte.")
        start_zeilen: list[str] = []
        funktionen: list[str] = []
        ereignisse: list[tuple[str, str]] = []     # (Bedingung, Funktionsname)
        benutzte_namen: set[str] = set()
        alle_zugewiesen: set[str] = set()
        for _ziel, bloecke, hut_id in skripte:
            self.blocke = bloecke
            self.zugewiesen = set()
            hut = bloecke[hut_id]
            op = hut["opcode"]
            if op in START_HUETE:
                start_zeilen += self.kette(hut.get("next"))
                alle_zugewiesen |= self.zugewiesen
                continue
            bedingung = self.ereignis_bedingung(hut)
            if bedingung is None:
                if op.startswith(("matatacarEvents_", "event_")):
                    self.warne(f"Das Ereignis '{op}' wird nicht unterstützt; das Skript wird übersprungen.")
                else:
                    self.warne(f"Ein Skript beginnt nicht mit einem Ereignis ('{op}'); es wird übersprungen.")
                continue
            fname = self.eindeutig(self.funktionsname(hut), benutzte_namen)
            rumpf = self.kette(hut.get("next"))
            kopf = [f"def {fname}() -> None:"]
            if self.zugewiesen:
                kopf.append("    global " + ", ".join(sorted(self.zugewiesen)))
            funktionen += kopf + _einruecken(rumpf) + ["", ""]
            ereignisse.append((bedingung, fname))
        zeilen = [f'"""Automatisch aus dem Scratch-Projekt "{name}" erzeugt (vincibot.scratch)."""']
        for baustein in ("math", "random"):
            if baustein in self.benutzt:
                zeilen.append(f"import {baustein}")
        zeilen += ["", "from vincibot import VinciBot", ""]
        for pname in sorted(self.variablen.values()):
            zeilen.append(f"{pname} = 0")
        if self.variablen:
            zeilen.append("")
        zeilen += [""] if self.variablen else []
        zeilen += funktionen
        zeilen += ["with VinciBot() as roboter:"]
        koerper = list(start_zeilen)
        if ereignisse:
            koerper += self.ereignisschleife(ereignisse)
        zeilen += _einruecken(koerper or ["pass"])
        return "\n".join(zeilen).rstrip() + "\n"

    @staticmethod
    def eindeutig(name: str, benutzt: set[str]) -> str:
        kandidat, nr = name, 2
        while kandidat in benutzt:
            kandidat, nr = f"{name}_{nr}", nr + 1
        benutzt.add(kandidat)
        return kandidat

    def funktionsname(self, hut: dict[str, Any]) -> str:
        if hut["opcode"] == "matatacarEvents_whenButtonPressed":
            taste = TASTEN.get(self.menu(hut, "BUTTON_KEY") or "", "taste")
            return f"bei_taste_{taste}"
        return "bei_" + re.sub(r"\W", "_", hut["opcode"].split("_", 1)[-1]).lower()

    def ereignis_bedingung(self, hut: dict[str, Any]) -> str | None:
        op = hut["opcode"]
        if op == "matatacarEvents_whenButtonPressed":
            taste = self.menu(hut, "BUTTON_KEY") or ""
            if taste in TASTEN:
                return f"roboter.taste_gedrueckt({TASTEN[taste]!r}) is True"
            self.warne(f"Taste '{taste}' kennt der VinciBot nicht.")
            return None
        if op == "matatacarEvents_whenObstacleDetected":
            nahe = f"roboter.hindernis_naeher_als({self.wert(hut, 'VALUE')}) is True"
            return nahe if self.menu(hut, "COMPARE") == "<" else f"not ({nahe})"
        if op == "matatacarEvents_whenColorDetected":
            deutsch = EN_FARBE_SENSOR.get(self.menu(hut, "COLOR_TYPE") or "")
            return f"roboter.sieht_farbe({deutsch!r}) is True" if deutsch else None
        return None

    @staticmethod
    def ereignisschleife(ereignisse: list[tuple[str, str]]) -> list[str]:
        zeilen = ["", "# Ereignisse: Tasten und Sensoren werden laufend abgefragt (Strg+C beendet)",
                  "ereignisse = ["]
        for bedingung, fname in ereignisse:
            zeilen.append(f"    (lambda: {bedingung}, {fname}),")
        zeilen += ["]", "vorher = [False] * len(ereignisse)", "try:", "    while True:",
                   "        for nr, (bedingung, aktion) in enumerate(ereignisse):",
                   "            jetzt = bedingung()",
                   "            if jetzt and not vorher[nr]:",
                   "                aktion()",
                   "            vorher[nr] = jetzt",
                   "        roboter.warte(0.1)",
                   "except KeyboardInterrupt:",
                   "    pass"]
        return zeilen


_KONSTANTEN = {"math_0to255_number", "note", "faceLed", "math_number", "math_integer",
               "math_whole_number", "math_positive_number", "math_angle", "text"}
_LISTEN_REPORTER = {
    "matatacarSound_getMoodList": "MOOD_LIST", "matatacarSound_getAnimalList": "ANIMAL_LIST",
    "matatacarSound_getTrafficList": "TRAFFIC_LIST", "matatacarSound_getGameList": "GAME_LIST",
    "matatacarSound_getOtherList": "OTHER_LIST",
}


def _lade_projekt(quelle: str | Path | bytes) -> tuple[dict[str, Any], str]:
    if isinstance(quelle, bytes):
        daten = quelle
        name = "Projekt"
    else:
        pfad = Path(quelle)
        daten = pfad.read_bytes()
        name = pfad.stem
    try:
        with zipfile.ZipFile(_BytesIO(daten)) as archiv:
            projekt = json.loads(archiv.read("project.json").decode("utf-8"))
    except (zipfile.BadZipFile, KeyError):
        try:
            projekt = json.loads(daten.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as fehler:
            raise UmwandlungsFehler("Das ist kein Scratch-Projekt (.mc oder .sb3).") from fehler
    if not isinstance(projekt, dict) or "targets" not in projekt:
        raise UmwandlungsFehler("Das ist kein Scratch-Projekt: 'targets' fehlt.")
    return projekt, name


class _BytesIO:
    """Minimaler Ersatz, damit zipfile aus Bytes lesen kann (ohne weiteren Import)."""
    def __new__(cls, daten: bytes) -> Any:
        import io
        return io.BytesIO(daten)


def scratch_zu_python(quelle: str | Path | bytes, name: str | None = None) -> Ergebnis:
    """Wandelt ein Scratch-Projekt (Datei oder Bytes) in Python-Text um."""
    projekt, dateiname = _lade_projekt(quelle)
    umwandler = _ZuPython([t for t in projekt["targets"]])
    code = umwandler.erzeuge(name or dateiname)
    return Ergebnis(code, umwandler.warnungen)


def scratch_datei_zu_python(eingabe: str | Path, ausgabe: str | Path | None = None) -> Ergebnis:
    """Liest `eingabe` (.mc/.sb3) und schreibt die Python-Datei (Standard: gleicher Name, .py)."""
    ergebnis = scratch_zu_python(eingabe)
    ziel = Path(ausgabe) if ausgabe else Path(eingabe).with_suffix(".py")
    _ = ziel.write_text(ergebnis.inhalt, encoding="utf-8")
    return ergebnis


# ============================================================================================
#  Python  ->  Scratch
# ============================================================================================
_SVG_BUEHNE = '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360"></svg>'
_SVG_FIGUR = ('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">'
              '<circle cx="24" cy="24" r="20" fill="#4c97ff"/></svg>')


class _Baumeister:
    """Baut die Scratch-Blöcke aus einem Python-Syntaxbaum."""

    def __init__(self, roboter_name: str) -> None:
        self.roboter: str = roboter_name
        self.bloecke: dict[str, dict[str, Any]] = {}
        self.variablen: dict[str, str] = {}      # Python-Name -> Scratch-ID
        self.warnungen: list[str] = []
        self.zaehler: int = 0
        self.erweiterungen: set[str] = set()

    # ------------------------------------------------------------------ Grundbausteine
    def warne(self, knoten: ast.AST | None, text: str) -> None:
        nummer = getattr(knoten, "lineno", None)
        zeile = f"Zeile {nummer}: " if nummer is not None else ""
        meldung = zeile + text
        if meldung not in self.warnungen:
            self.warnungen.append(meldung)

    def neue_id(self) -> str:
        self.zaehler += 1
        return f"b{self.zaehler:05d}"

    def block(self, opcode: str, eingaben: dict[str, Any] | None = None,
              felder: dict[str, Any] | None = None, schatten: bool = False) -> str:
        bid = self.neue_id()
        self.bloecke[bid] = {"opcode": opcode, "next": None, "parent": None,
                             "inputs": eingaben or {}, "fields": felder or {}, "shadow": schatten,
                             "topLevel": False}
        if opcode.startswith("matatacar"):
            self.erweiterungen.add(opcode.split("_", 1)[0])
        return bid

    def eltern_setzen(self, eingaben: dict[str, Any], eltern: str) -> None:
        for wert in eingaben.values():
            if isinstance(wert, list) and len(wert) >= 2 and isinstance(wert[1], str):
                self.bloecke[wert[1]]["parent"] = eltern
            if isinstance(wert, list) and len(wert) >= 2 and isinstance(wert[1], list) and wert[1] and wert[1][0] == 12:
                continue

    def befehl(self, opcode: str, eingaben: dict[str, Any] | None = None,
               felder: dict[str, Any] | None = None) -> str:
        bid = self.block(opcode, eingaben, felder)
        self.eltern_setzen(eingaben or {}, bid)
        return bid

    def menue(self, erweiterung: str, name: str, wert: str) -> list[Any]:
        bid = self.block(f"{erweiterung}_menu_{name}", felder={name: [wert, None]}, schatten=True)
        return [1, bid]

    def zahl(self, wert: object, art: int = 4) -> list[Any]:
        return [1, [art, str(wert)]]

    def text(self, wert: str) -> list[Any]:
        return [1, [10, wert]]

    def variable(self, name: str) -> str:
        if name not in self.variablen:
            self.variablen[name] = f"var{len(self.variablen) + 1:03d}"
        return self.variablen[name]

    # ------------------------------------------------------------------ Ausdrücke -> Eingaben
    def konstante(self, knoten: ast.expr) -> object | None:
        try:
            return ast.literal_eval(knoten)
        except (ValueError, SyntaxError):
            return None

    def eingabe_zahl(self, knoten: ast.expr) -> list[Any]:
        """Zahl-Eingabe: feste Zahl oder Rechenausdruck/Variable/Sensor."""
        wert = self.konstante(knoten)
        if isinstance(wert, (int, float)) and not isinstance(wert, bool):
            return self.zahl(int(wert) if isinstance(wert, float) and wert.is_integer() else wert)
        return self.eingabe_ausdruck(knoten)

    def eingabe_ausdruck(self, knoten: ast.expr) -> list[Any]:
        """Ausdruck als Eingabe [3, Block, Ersatz] (Block darf auch eine Variable sein)."""
        wert = self.konstante(knoten)
        if isinstance(wert, str):
            return self.text(wert)
        if isinstance(wert, (int, float)) and not isinstance(wert, bool):
            return self.zahl(wert)
        if isinstance(knoten, ast.Name):
            return [3, [12, knoten.id, self.variable(knoten.id)], [4, "0"]]
        bid = self.ausdruck_block(knoten)
        if bid is None:
            return self.zahl(0)
        return [3, bid, [4, "0"]]

    def bedingung_eingabe(self, knoten: ast.expr) -> list[Any] | None:
        bid = self.bedingung_block(knoten)
        return None if bid is None else [2, bid]

    # ------------------------------------------------------------------ Ausdrucksblöcke
    def ausdruck_block(self, k: ast.expr) -> str | None:
        if isinstance(k, ast.BinOp):
            ops: dict[type[ast.operator], str] = {ast.Add: "operator_add", ast.Sub: "operator_subtract", ast.Mult: "operator_multiply",
                   ast.Div: "operator_divide", ast.Mod: "operator_mod"}
            op = ops.get(type(k.op))
            if op is None:
                self.warne(k, f"Rechenzeichen {type(k.op).__name__} wird nicht unterstützt.")
                return None
            return self.befehl(op, {"NUM1": self.eingabe_zahl(k.left), "NUM2": self.eingabe_zahl(k.right)})
        if isinstance(k, ast.UnaryOp) and isinstance(k.op, ast.USub):
            return self.befehl("operator_subtract", {"NUM1": self.zahl(0), "NUM2": self.eingabe_zahl(k.operand)})
        if isinstance(k, ast.Call):
            return self.aufruf_ausdruck(k)
        if isinstance(k, (ast.Compare, ast.BoolOp, ast.UnaryOp)):
            return self.bedingung_block(k)
        self.warne(k, "Dieser Ausdruck wird nicht unterstützt.")
        return None

    def aufruf_ausdruck(self, k: ast.Call) -> str | None:
        name = self.aufruf_name(k)
        if name == "random.randint" and len(k.args) == 2:
            return self.befehl("operator_random", {"FROM": self.eingabe_zahl(k.args[0]),
                                                   "TO": self.eingabe_zahl(k.args[1])})
        if name in ("round", "int") and len(k.args) == 1:
            return self.befehl("operator_round", {"NUM": self.eingabe_zahl(k.args[0])})
        methode = self.roboter_methode(k)
        if methode == "abstand":
            return self.befehl("matatacarSensors_getObstacleDistance")
        if methode == "lautstaerke_umgebung":
            return self.befehl("matatacarSensors_loudness")
        if methode == "farbwert" and k.args:
            farbe = self.konstante(k.args[0])
            kanal = {"rot": "red", "gruen": "green", "blau": "blue"}.get(str(farbe))
            if kanal:
                return self.befehl("matatacarSensors_getRGBColor",
                                   {"COLOR_CHANNEL": self.menue("matatacarSensors", "colorChannel", kanal)})
        if methode in ("sieht_farbe", "taste_gedrueckt", "hindernis_naeher_als"):
            return self.bedingung_block(k)
        self.warne(k, f"Der Aufruf {name or 'dieser Aufruf'}() wird als Wert nicht unterstützt.")
        return None

    def bedingung_block(self, k: ast.expr) -> str | None:
        if isinstance(k, ast.Compare) and len(k.ops) == 1:
            links, rechts = k.left, k.comparators[0]
            op = k.ops[0]
            tabelle: dict[type[ast.cmpop], str] = {ast.Lt: "operator_lt", ast.Gt: "operator_gt",
                                                   ast.Eq: "operator_equals"}
            if type(op) in tabelle:
                return self.befehl(tabelle[type(op)], {"OPERAND1": self.eingabe_ausdruck(links),
                                                      "OPERAND2": self.eingabe_ausdruck(rechts)})
            if isinstance(op, ast.LtE):     # a <= b  ==  nicht (a > b)
                innen = self.befehl("operator_gt", {"OPERAND1": self.eingabe_ausdruck(links),
                                                    "OPERAND2": self.eingabe_ausdruck(rechts)})
                return self.befehl("operator_not", {"OPERAND": [2, innen]})
            if isinstance(op, ast.GtE):
                innen = self.befehl("operator_lt", {"OPERAND1": self.eingabe_ausdruck(links),
                                                    "OPERAND2": self.eingabe_ausdruck(rechts)})
                return self.befehl("operator_not", {"OPERAND": [2, innen]})
            if isinstance(op, ast.NotEq):
                innen = self.befehl("operator_equals", {"OPERAND1": self.eingabe_ausdruck(links),
                                                        "OPERAND2": self.eingabe_ausdruck(rechts)})
                return self.befehl("operator_not", {"OPERAND": [2, innen]})
            self.warne(k, "Dieser Vergleich wird nicht unterstützt.")
            return None
        if isinstance(k, ast.BoolOp):
            opcode = "operator_and" if isinstance(k.op, ast.And) else "operator_or"
            aktuell = self.bedingung_block(k.values[0])
            for weiter in k.values[1:]:
                rechts = self.bedingung_block(weiter)
                if aktuell is None or rechts is None:
                    return None
                aktuell = self.befehl(opcode, {"OPERAND1": [2, aktuell], "OPERAND2": [2, rechts]})
            return aktuell
        if isinstance(k, ast.UnaryOp) and isinstance(k.op, ast.Not):
            innen = self.bedingung_block(k.operand)
            return None if innen is None else self.befehl("operator_not", {"OPERAND": [2, innen]})
        if isinstance(k, ast.Call):
            methode = self.roboter_methode(k)
            if methode == "hindernis_naeher_als" and k.args:
                return self.befehl("matatacarSensors_isObstaclesAhead", {
                    "COMPARE": self.menue("matatacarSensors", "compareDir", "<"),
                    "VALUE": self.eingabe_zahl(k.args[0])})
            if methode == "sieht_farbe" and k.args:
                deutsch = self.konstante(k.args[0])
                englisch = FARBEN_SENSOR.get(str(deutsch))
                if englisch:
                    return self.befehl("matatacarSensors_recognizeColor", {
                        "COLOR_TYPE": self.menue("matatacarSensors", "colorType", englisch)})
                self.warne(k, f"Die Farbe {deutsch!r} kennt der Farbsensor nicht.")
                return None
            if methode == "taste_gedrueckt" and k.args:
                taste = TASTEN_UMGEKEHRT.get(str(self.konstante(k.args[0])))
                if taste:
                    return self.befehl("matatacarSensors_isButtonPressed", {
                        "BUTTON_KEY": self.menue("matatacarSensors", "buttonKey", taste)})
            self.warne(k, "Diese Bedingung wird nicht unterstützt.")
            return None
        self.warne(k, "Diese Bedingung wird nicht unterstützt.")
        return None

    # ------------------------------------------------------------------ Hilfen für Aufrufe
    def aufruf_name(self, k: ast.Call) -> str:
        teile: list[str] = []
        f: ast.expr = k.func
        while isinstance(f, ast.Attribute):
            teile.append(f.attr)
            f = f.value
        if isinstance(f, ast.Name):
            teile.append(f.id)
        return ".".join(reversed(teile))

    def roboter_methode(self, k: ast.Call) -> str | None:
        if (isinstance(k.func, ast.Attribute) and isinstance(k.func.value, ast.Name)
                and k.func.value.id == self.roboter):
            return k.func.attr
        return None

    def argument(self, k: ast.Call, pos: int, name: str, standard: ast.expr | None = None) -> ast.expr | None:
        if pos < len(k.args):
            return k.args[pos]
        for kw in k.keywords:
            if kw.arg == name:
                return kw.value
        return standard

    def fest(self, k: ast.Call, pos: int, name: str, standard: object = None) -> object:
        arg = self.argument(k, pos, name)
        return standard if arg is None else self.konstante(arg)

    # ------------------------------------------------------------------ Anweisungen
    def anweisungen(self, liste: list[ast.stmt]) -> list[str]:
        ids: list[str] = []
        for a in liste:
            ids += self.anweisung(a)
        return ids

    def verketten(self, ids: list[str], eltern: str | None = None) -> str | None:
        for vorher, nachher in zip(ids, ids[1:]):
            self.bloecke[vorher]["next"] = nachher
            self.bloecke[nachher]["parent"] = vorher
        if ids and eltern:
            self.bloecke[ids[0]]["parent"] = eltern
        return ids[0] if ids else None

    def anweisung(self, a: ast.stmt) -> list[str]:
        if isinstance(a, (ast.Import, ast.ImportFrom, ast.Pass)):
            return []
        if isinstance(a, ast.Expr):
            if isinstance(a.value, ast.Constant):          # Docstring
                return []
            if isinstance(a.value, ast.Call):
                bid = self.aufruf_anweisung(a.value)
                return [bid] if bid else []
        if isinstance(a, ast.With):
            return self.anweisungen(a.body)
        if isinstance(a, ast.Try):
            return self.anweisungen(a.body)
        if isinstance(a, ast.For):
            return self.for_schleife(a)
        if isinstance(a, ast.While):
            return self.while_schleife(a)
        if isinstance(a, ast.If):
            return self.wenn(a)
        if isinstance(a, ast.Assign) and len(a.targets) == 1 and isinstance(a.targets[0], ast.Name):
            return self.zuweisung(a.targets[0].id, a.value)
        if isinstance(a, ast.AugAssign) and isinstance(a.target, ast.Name):
            return self.erweiterte_zuweisung(a)
        self.warne(a, f"'{type(a).__name__}' wird nicht unterstützt und übersprungen.")
        return []

    def zuweisung(self, name: str, wert: ast.expr) -> list[str]:
        if (isinstance(wert, ast.Call) and self.aufruf_name(wert) == "VinciBot"):
            return []
        eingabe = self.eingabe_ausdruck(wert)
        bid = self.block("data_setvariableto", {"VALUE": eingabe},
                         {"VARIABLE": [name, self.variable(name)]})
        self.eltern_setzen({"VALUE": eingabe}, bid)
        return [bid]

    def erweiterte_zuweisung(self, a: ast.AugAssign) -> list[str]:
        name = a.target.id if isinstance(a.target, ast.Name) else ""
        if isinstance(a.op, (ast.Add, ast.Sub)):
            wert = a.value
            if isinstance(a.op, ast.Sub):
                eingabe = self.eingabe_ausdruck(ast.UnaryOp(op=ast.USub(), operand=wert))
            else:
                eingabe = self.eingabe_zahl(wert)
            bid = self.block("data_changevariableby", {"VALUE": eingabe},
                             {"VARIABLE": [name, self.variable(name)]})
            self.eltern_setzen({"VALUE": eingabe}, bid)
            return [bid]
        neu = ast.BinOp(left=ast.Name(id=name), op=a.op, right=a.value)
        return self.zuweisung(name, neu)

    def for_schleife(self, a: ast.For) -> list[str]:
        if (isinstance(a.iter, ast.Call) and self.aufruf_name(a.iter) == "range"
                and len(a.iter.args) == 1 and isinstance(a.target, ast.Name)):
            anzahl = self.eingabe_zahl(a.iter.args[0])
            rumpf = self.verketten(self.anweisungen(a.body))
            eingaben: dict[str, Any] = {"TIMES": anzahl}
            if rumpf:
                eingaben["SUBSTACK"] = [2, rumpf]
            bid = self.befehl("control_repeat", eingaben)
            return [bid]
        self.warne(a, "Nur 'for _ in range(n)' wird unterstützt; die Schleife wird übersprungen.")
        return []

    def while_schleife(self, a: ast.While) -> list[str]:
        rumpf = self.verketten(self.anweisungen(a.body))
        if isinstance(a.test, ast.Constant) and a.test.value is True:
            eingaben: dict[str, Any] = {}
            if rumpf:
                eingaben["SUBSTACK"] = [2, rumpf]
            return [self.befehl("control_forever", eingaben)]
        bedingung = self.bedingung_block(ast.UnaryOp(op=ast.Not(), operand=a.test))
        if bedingung is None:
            return []
        eingaben = {"CONDITION": [2, bedingung]}
        if rumpf:
            eingaben["SUBSTACK"] = [2, rumpf]
        return [self.befehl("control_repeat_until", eingaben)]

    def wenn(self, a: ast.If) -> list[str]:
        bedingung = self.bedingung_block(a.test)
        if bedingung is None:
            return []
        dann = self.verketten(self.anweisungen(a.body))
        sonst = self.verketten(self.anweisungen(a.orelse))
        eingaben: dict[str, Any] = {"CONDITION": [2, bedingung]}
        if dann:
            eingaben["SUBSTACK"] = [2, dann]
        if sonst:
            eingaben["SUBSTACK2"] = [2, sonst]
        return [self.befehl("control_if_else" if sonst else "control_if", eingaben)]

    # ------------------------------------------------------------------ Roboter-Befehle
    def aufruf_anweisung(self, k: ast.Call) -> str | None:
        name = self.aufruf_name(k)
        if name in ("time.sleep", "sleep"):
            if k.args:
                return self.befehl("control_wait", {"DURATION": self.eingabe_zahl(k.args[0])})
            return None
        methode = self.roboter_methode(k)
        if methode is None:
            self.warne(k, f"Der Aufruf {name or 'dieser Aufruf'}() wird nicht unterstützt.")
            return None
        if methode in ("trennen", "verbinden"):
            return None
        bauer = _METHODEN.get(methode)
        if bauer is None:
            self.warne(k, f"roboter.{methode}() gibt es in Scratch nicht und wird übersprungen.")
            return None
        try:
            return bauer(self, k)
        except _NichtUnterstuetzt as fehler:
            self.warne(k, f"roboter.{methode}(): {fehler}")
            return None


class _NichtUnterstuetzt(Exception):
    pass


def _fest_text(b: _Baumeister, k: ast.Call, pos: int, name: str, tabelle: dict[str, str], art: str) -> str:
    wert = b.fest(k, pos, name)
    if not isinstance(wert, str):
        raise _NichtUnterstuetzt(f"{art} muss fest im Programm stehen (kein Wert aus einer Variablen).")
    englisch = tabelle.get(wert.lower())
    if englisch is None:
        raise _NichtUnterstuetzt(f"{art} '{wert}' ist unbekannt.")
    return englisch


def _strecke(richtung: str) -> Callable[[_Baumeister, ast.Call], str]:
    def bauen(b: _Baumeister, k: ast.Call) -> str:
        standard = ast.Constant(value=10)
        wert = b.argument(k, 0, "zentimeter", standard)
        assert wert is not None
        return b.befehl("matatacarMotion_movePosition", {
            "DIRECTION": b.menue("matatacarMotion", "motionTrend", richtung),
            "VALUE": b.eingabe_zahl(wert),
            "POS_UNIT": b.menue("matatacarMotion", "motionPosUnit", "cm")})
    return bauen


def _drehen(richtung: str) -> Callable[[_Baumeister, ast.Call], str]:
    def bauen(b: _Baumeister, k: ast.Call) -> str:
        wert = b.argument(k, 0, "grad", ast.Constant(value=90))
        assert wert is not None
        return b.befehl("matatacarMotion_moveAngle", {
            "DIRECTION": b.menue("matatacarMotion", "motionTurn", richtung),
            "VALUE": b.eingabe_zahl(wert),
            "ANGLE_UNIT": b.menue("matatacarMotion", "motionAngleUint", "degrees")})
    return bauen


def _fahre(b: _Baumeister, k: ast.Call) -> str:
    umgekehrt = {v: key for key, v in RICHTUNG_FAHRE.items()}
    richtung = _fest_text(b, k, 0, "richtung", umgekehrt, "Die Richtung")
    tempo = b.argument(k, 1, "tempo", ast.Constant(value=50))
    assert tempo is not None
    return b.befehl("matatacarMotion_startMoving", {
        "DIRECTION": b.menue("matatacarMotion", "motionDirection", richtung),
        "SPEED": b.eingabe_zahl(tempo)})


def _licht(b: _Baumeister, k: ast.Call) -> str:
    if not k.args and not k.keywords:
        raise _NichtUnterstuetzt("Es fehlt die Farbe.")
    arg = b.argument(k, 0, "farbe")
    assert arg is not None
    wert = b.konstante(arg)
    if isinstance(wert, str):
        rgb = FARBEN.get(wert.lower())
        if rgb is None:
            raise _NichtUnterstuetzt(f"Die Farbe '{wert}' ist unbekannt.")
    elif isinstance(wert, tuple) and len(wert) == 3 and all(isinstance(x, int) for x in wert):
        rgb = (wert[0], wert[1], wert[2])
    elif isinstance(arg, ast.Tuple) and len(arg.elts) == 3:
        # Farbwerte aus Variablen/Rechnungen: getrennte Eingaben
        kanaele = [_schatten_zahl(b, e) for e in arg.elts]
        return b.befehl("matatacarLight_rgbLedAllSet1", {
            "RED_VALUE": kanaele[0], "GREEN_VALUE": kanaele[1], "BLUE_VALUE": kanaele[2]})
    else:
        raise _NichtUnterstuetzt("Die Farbe muss ein Name oder drei Zahlen sein.")
    hexwert = "#%02x%02x%02x" % rgb
    return b.befehl("matatacarLight_rgbLedAllSet", {"COLOR": [1, [9, hexwert]]})


def _schatten_zahl(b: _Baumeister, k: ast.expr) -> list[Any]:
    """Eingabe für Felder, die in Scratch einen Zahlen-Schatten (0-255) haben."""
    wert = b.konstante(k)
    if isinstance(wert, (int, float)) and not isinstance(wert, bool):
        schatten = b.block("math_0to255_number", felder={"NUM": [str(int(wert)), None]}, schatten=True)
        return [1, schatten]
    schatten = b.block("math_0to255_number", felder={"NUM": ["0", None]}, schatten=True)
    ausdruck = b.eingabe_ausdruck(k)
    if ausdruck[0] == 3:
        return [3, ausdruck[1], [1, schatten][1]]
    return ausdruck


def _bild_bits(b: _Baumeister, k: ast.Call, pos: int) -> str:
    wert = b.fest(k, pos, "zeilen")
    if (not isinstance(wert, list) or len(wert) != 8                                 
            or not all(isinstance(z, str) and len(z) == 16 for z in wert)):           
        raise _NichtUnterstuetzt("Das Bild muss fest im Programm stehen: 8 Zeilen mit je 16 Zeichen.")
    return "".join("1" if zeichen == "#" else "0" for zeile in wert for zeichen in zeile)


def _bild(b: _Baumeister, k: ast.Call) -> str:
    bits = _bild_bits(b, k, 0)
    feld = b.block("faceLed", felder={"FACE_LED": [bits, None]}, schatten=True)
    return b.befehl("matatacarLight_displayShowImage", {"PANEL": [1, feld]})


def _bild_zeit(b: _Baumeister, k: ast.Call) -> str:
    bits = _bild_bits(b, k, 0)
    feld = b.block("faceLed", felder={"FACE_LED": [bits, None]}, schatten=True)
    sekunden = b.argument(k, 1, "sekunden", ast.Constant(value=2))
    assert sekunden is not None
    return b.befehl("matatacarLight_displayShowImageWithTime",
                    {"PANEL": [1, feld], "TIME": b.eingabe_zahl(sekunden)})


def _text(opcode: str, eingabe: str) -> Callable[[_Baumeister, ast.Call], str]:
    def bauen(b: _Baumeister, k: ast.Call) -> str:
        arg = b.argument(k, 0, "text", ast.Constant(value=""))
        assert arg is not None
        return b.befehl(opcode, {eingabe: b.eingabe_ausdruck(arg)})
    return bauen


def _einfach_zahl(opcode: str, eingabe: str, name: str, standard: int) -> Callable[[_Baumeister, ast.Call], str]:
    def bauen(b: _Baumeister, k: ast.Call) -> str:
        arg = b.argument(k, 0, name, ast.Constant(value=standard))
        assert arg is not None
        return b.befehl(opcode, {eingabe: b.eingabe_zahl(arg)})
    return bauen


def _benannt(opcode: str, erweiterung: str, menue: str, eingabe: str, tabelle: dict[str, str],
             art: str) -> Callable[[_Baumeister, ast.Call], str]:
    def bauen(b: _Baumeister, k: ast.Call) -> str:
        englisch = _fest_text(b, k, 0, "name", tabelle, art)
        return b.befehl(opcode, {eingabe: b.menue(erweiterung, menue, englisch)})
    return bauen


def _pixel(b: _Baumeister, k: ast.Call) -> str:
    x, y = b.argument(k, 0, "spalte"), b.argument(k, 1, "zeile")
    helligkeit = b.argument(k, 2, "helligkeit", ast.Constant(value=100))
    if x is None or y is None or helligkeit is None:
        raise _NichtUnterstuetzt("Spalte und Zeile fehlen.")
    return b.befehl("matatacarLight_displaySetPixel", {
        "X_AXIS": b.eingabe_zahl(x), "Y_AXIS": b.eingabe_zahl(y), "BRIGHTNESS": b.eingabe_zahl(helligkeit)})


def _ton_hoehe(b: _Baumeister, k: ast.Call) -> str:
    midi = b.fest(k, 0, "midi_nummer")
    if not isinstance(midi, int):
        raise _NichtUnterstuetzt("Die Notennummer muss fest im Programm stehen.")
    schlaege = b.argument(k, 1, "schlaege", ast.Constant(value=1))
    assert schlaege is not None
    note = b.block("note", felder={"NOTE": [str(midi), None]}, schatten=True)
    return b.befehl("matatacarMusic_playNoteForBeats", {"NOTE": [1, note], "BEATS": b.eingabe_zahl(schlaege)})


def _ton(b: _Baumeister, k: ast.Call) -> str:
    halbtoene = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "h": 11}
    name = b.fest(k, 0, "note", "c")
    oktave = b.fest(k, 2, "oktave", 4)
    if not isinstance(name, str) or name.lower() not in halbtoene or not isinstance(oktave, int):
        raise _NichtUnterstuetzt("Note und Oktave müssen fest im Programm stehen.")
    midi = 12 * (oktave + 1) + halbtoene[name.lower()]
    schlaege = b.argument(k, 1, "schlaege", ast.Constant(value=1))
    assert schlaege is not None
    note = b.block("note", felder={"NOTE": [str(midi), None]}, schatten=True)
    return b.befehl("matatacarMusic_playNoteForBeats", {"NOTE": [1, note], "BEATS": b.eingabe_zahl(schlaege)})


def _sprich(b: _Baumeister, k: ast.Call) -> str:
    arg = b.argument(k, 0, "text", ast.Constant(value=""))
    assert arg is not None
    warten = b.fest(k, 1, "warten", True)
    return b.befehl("matatacarSound_sayUntilDone" if warten else "matatacarSound_say",
                    {"MESSAGE": b.eingabe_ausdruck(arg)})


_METHODEN: dict[str, Callable[[_Baumeister, ast.Call], str]] = {
    "vorwaerts": _strecke("forward"), "rueckwaerts": _strecke("backward"),
    "links": _drehen("left"), "rechts": _drehen("right"),
    "fahre": _fahre,
    "stoppe": lambda b, k: b.befehl("matatacarMotion_motionStopMoving"),
    "licht": _licht,
    "licht_aus": lambda b, k: b.befehl("matatacarLight_rgbLedAllOff"),
    "schreibe": _text("matatacarLight_displayWriteText", "TEXT"),
    "zeige_bild": _bild, "zeige_bild_fuer": _bild_zeit,
    "zeige_pixel": _pixel,
    "display_aus": lambda b, k: b.befehl("matatacarLight_displayTurnOff"),
    "display_helligkeit": _einfach_zahl("matatacarLight_displaySetBrightness", "BRIGHTNESS", "prozent", 100),
    "gefuehl": _benannt("matatacarPerformance_doEmotion", "matatacarPerformance", "emotionIndex",
                        "EMOTION_INDEX", GEFUEHLE, "Das Gefühl"),
    "tanze": _benannt("matatacarPerformance_doDance", "matatacarPerformance", "danceIndex",
                      "DANCE_INDEX", TAENZE, "Der Tanz"),
    "bewege_dich": _benannt("matatacarPerformance_doAction", "matatacarPerformance", "actionIndex",
                            "ACTION_INDEX", BEWEGUNGEN, "Die Bewegung"),
    "sprich": _sprich,
    "ton_hoehe": _ton_hoehe, "ton": _ton,
    "pause": _einfach_zahl("matatacarMusic_restForBeats", "BEATS", "schlaege", 1),
    "warte": lambda b, k: b.befehl("control_wait", {"DURATION": b.eingabe_zahl(
        k.args[0] if k.args else ast.Constant(value=1))}),
}


def _projekt_rahmen(blocke: dict[str, dict[str, Any]], variablen: dict[str, str],
                    erweiterungen: set[str], name: str) -> tuple[dict[str, Any], dict[str, bytes]]:
    buehne_svg = _SVG_BUEHNE.encode("utf-8")
    figur_svg = _SVG_FIGUR.encode("utf-8")
    buehne_id = hashlib.md5(buehne_svg).hexdigest()
    figur_id = hashlib.md5(figur_svg).hexdigest()
    variablen_json = {vid: [pname, 0] for pname, vid in variablen.items()}
    buehne = {"isStage": True, "name": "Stage", "variables": variablen_json, "lists": {}, "broadcasts": {},
              "blocks": {}, "comments": {}, "currentCostume": 0,
              "costumes": [{"name": "Bühnenbild1", "dataFormat": "svg", "assetId": buehne_id,
                            "md5ext": f"{buehne_id}.svg", "rotationCenterX": 240, "rotationCenterY": 180}],
              "sounds": [], "volume": 100, "layerOrder": 0, "tempo": 60, "videoTransparency": 50,
              "videoState": "on", "textToSpeechLanguage": None}
    figur = {"isStage": False, "name": "Figur1", "variables": {}, "lists": {}, "broadcasts": {},
             "blocks": blocke, "comments": {}, "currentCostume": 0,
             "costumes": [{"name": "Kostüm1", "bitmapResolution": 1, "dataFormat": "svg", "assetId": figur_id,
                           "md5ext": f"{figur_id}.svg", "rotationCenterX": 24, "rotationCenterY": 24}],
             "sounds": [], "volume": 100, "layerOrder": 1, "visible": True, "x": 0, "y": 0, "size": 100,
             "direction": 90, "draggable": False, "rotationStyle": "all around"}
    projekt = {"targets": [buehne, figur], "monitors": [], "extensions": sorted(erweiterungen),
               "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": f"vincibot {name}"}}
    return projekt, {f"{buehne_id}.svg": buehne_svg, f"{figur_id}.svg": figur_svg}


def python_zu_scratch(quelltext: str, name: str = "Projekt") -> Ergebnis:
    """Wandelt Python-Text in ein Scratch-Projekt um. `Ergebnis.inhalt` ist ein Wörterbuch
    `{"project.json": ..., "assets": {...}}`; zum Speichern `python_datei_zu_scratch` nutzen."""
    try:
        baum = ast.parse(quelltext)
    except SyntaxError as fehler:
        raise UmwandlungsFehler(f"Das Python-Programm hat einen Fehler in Zeile {fehler.lineno}: "
                                f"{fehler.msg}") from fehler
    roboter = "roboter"
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.With):
            for eintrag in knoten.items:
                if (isinstance(eintrag.context_expr, ast.Call) and isinstance(eintrag.optional_vars, ast.Name)
                        and getattr(eintrag.context_expr.func, "id", "") == "VinciBot"):
                    roboter = eintrag.optional_vars.id
        elif (isinstance(knoten, ast.Assign) and isinstance(knoten.value, ast.Call)
              and getattr(knoten.value.func, "id", "") == "VinciBot"
              and isinstance(knoten.targets[0], ast.Name)):
            roboter = knoten.targets[0].id
    baumeister = _Baumeister(roboter)
    ids: list[str] = []
    for anweisung in baum.body:
        if isinstance(anweisung, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            baumeister.warne(anweisung, "Funktionen und Klassen werden nicht umgewandelt (Scratch-Block 'Meine Blöcke' fehlt).")
            continue
        ids += baumeister.anweisungen([anweisung])
    hut = baumeister.block("matatacarEvents_whenRobotStart")
    baumeister.bloecke[hut].update({"topLevel": True, "x": 60, "y": 40})
    erste = baumeister.verketten(ids, hut)
    baumeister.bloecke[hut]["next"] = erste
    baumeister.erweiterungen.add("matatacarEvents")
    projekt, assets = _projekt_rahmen(baumeister.bloecke, baumeister.variablen, baumeister.erweiterungen, name)
    return Ergebnis({"project.json": projekt, "assets": assets}, baumeister.warnungen)


def python_datei_zu_scratch(eingabe: str | Path, ausgabe: str | Path | None = None) -> Ergebnis:
    """Liest eine Python-Datei und schreibt ein Scratch-Projekt (Standard: gleicher Name, .mc)."""
    pfad = Path(eingabe)
    ergebnis = python_zu_scratch(pfad.read_text(encoding="utf-8"), pfad.stem)
    ziel = Path(ausgabe) if ausgabe else pfad.with_suffix(".mc")
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as archiv:
        archiv.writestr("project.json", json.dumps(ergebnis.inhalt["project.json"], ensure_ascii=False))
        for dateiname, inhalt in ergebnis.inhalt["assets"].items():
            archiv.writestr(dateiname, inhalt)
    return ergebnis


# ============================================================================================
#  Kommandozeile
# ============================================================================================
def haupt(argumente: list[str] | None = None) -> int:
    args = sys.argv[1:] if argumente is None else argumente
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 1
    eingabe = Path(args[0])
    ausgabe = Path(args[1]) if len(args) > 1 else None
    try:
        if eingabe.suffix.lower() == ".py":
            ergebnis = python_datei_zu_scratch(eingabe, ausgabe)
            ziel = ausgabe or eingabe.with_suffix(".mc")
        else:
            ergebnis = scratch_datei_zu_python(eingabe, ausgabe)
            ziel = ausgabe or eingabe.with_suffix(".py")
    except (UmwandlungsFehler, OSError) as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 1
    print(f"Geschrieben: {ziel}")
    for warnung in ergebnis.warnungen:
        print(f"Warnung: {warnung}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(haupt())
