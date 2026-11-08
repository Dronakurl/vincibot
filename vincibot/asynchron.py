"""Die volle Schnittstelle zum VinciBot mit `async`/`await`.

Damit kann der Roboter mehrere Dinge gleichzeitig tun, zum Beispiel fahren und dabei blinken.
Für den Einstieg ist die einfachere Klasse `VinciBot` (ohne async) gedacht.

Beispiel:
    import asyncio
    from vincibot import VinciBotAsync

    async def haupt():
        async with VinciBotAsync() as roboter:
            await asyncio.gather(roboter.vorwaerts(20), roboter.licht("rot"))

    asyncio.run(haupt())
"""
from __future__ import annotations

import asyncio
import math
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from types import TracebackType

from ._protokoll import SEQUENZ, Sensorwerte, text_literal
from ._verbindung import Antwort, Verbindung
from ._typen import (Bewegung, Bodensensor, DisplayRichtung, Drehrichtung, Einheit, Farbe, Farbkanal,
                     Fernbedienungstaste, FahrRichtung, Gefuehl, Geraeusch, Instrument, Lied, Linienfarbe,
                     Note, Position, Rad, Seite, SensorFarbe, Tanz, Taste)
from ._woerter import (BEWEGUNGEN, FARBEN_SENSOR, GEFUEHLE, GERAEUSCHE, INSTRUMENTE, LIEDER,
                       NOTEN, POSITIONEN, TAENZE, RoboterFehler, farbe_umrechnen, waehle)


class VinciBotAsync:
    """Dein Roboter – mit `await` bedienen. Alle Methoden sind `async`."""

    def __init__(self, adresse: str | None = None, suchdauer: float = 15) -> None:
        """adresse: nur nötig, wenn mehrere Roboter in der Nähe sind (z. B. "AA:BB:CC:DD:EE:FF").
        suchdauer: Wie viele Sekunden nach dem Roboter gesucht wird."""
        self._verbindung: Verbindung = Verbindung(adresse=adresse, suchdauer=suchdauer)

    # ------------------------------------------------------------ Verbindung
    async def verbinden(self) -> None:
        """Verbindet sich mit dem Roboter (macht `async with` automatisch)."""
        await self._verbindung.verbinden()

    async def trennen(self) -> None:
        """Beendet die Verbindung zum Roboter."""
        await self._verbindung.trennen()

    async def __aenter__(self) -> "VinciBotAsync":
        await self.verbinden()
        return self

    async def __aexit__(self, typ: type[BaseException] | None,
                        wert: BaseException | None,
                        spur: TracebackType | None) -> None:
        await self.trennen()

    # ------------------------------------------------------------ Hilfsmittel (intern)
    async def _antwort(self, code: str, art: str, wartezeit: float = 15) -> Antwort | None:
        antwort = await self._verbindung.befehl(code, SEQUENZ[art], wartezeit)
        if antwort is not None and antwort.fehler:
            raise RoboterFehler(f"Der Roboter konnte das nicht ausführen ({antwort.text}).")
        return antwort

    async def _befehl(self, code: str, art: str, wartezeit: float = 15) -> None:
        _ = await self._antwort(code, art, wartezeit)

    async def _text(self, ausdruck: str) -> str | None:
        antwort = await self._antwort(ausdruck, "abfrage", 5)
        return None if antwort is None else antwort.text.strip()

    async def _zahl(self, ausdruck: str) -> float | None:
        text = await self._text(ausdruck)
        try:
            return None if text is None else float(text)
        except ValueError:
            return None

    async def _ganzzahl(self, ausdruck: str) -> int | None:
        zahl = await self._zahl(ausdruck)
        return None if zahl is None else int(zahl)

    async def _wahrheit(self, ausdruck: str) -> bool | None:
        text = await self._text(ausdruck)
        return None if text is None else text == "True"

    async def warte(self, sekunden: float) -> None:
        """Wartet, ohne etwas zu tun."""
        await asyncio.sleep(sekunden)

    # ------------------------------------------------------------ Fahren
    async def vorwaerts(self, zentimeter: float = 10) -> None:
        """Fährt die angegebene Strecke nach vorne."""
        await self._befehl(f'motion.move_position("forward", {zentimeter}, "cm")', "strecke", 30)

    async def rueckwaerts(self, zentimeter: float = 10) -> None:
        """Fährt die angegebene Strecke rückwärts."""
        await self._befehl(f'motion.move_position("backward", {zentimeter}, "cm")', "strecke", 30)

    async def links(self, grad: float = 90) -> None:
        """Dreht sich auf der Stelle nach links."""
        await self._befehl(f'motion.move_angle("left", {grad}, "degrees")', "winkel", 30)

    async def rechts(self, grad: float = 90) -> None:
        """Dreht sich auf der Stelle nach rechts."""
        await self._befehl(f'motion.move_angle("right", {grad}, "degrees")', "winkel", 30)

    async def fahre(self, richtung: FahrRichtung = "vorwaerts", tempo: int = 50) -> None:
        """Fährt immer weiter, bis du `stoppe()` aufrufst.

        richtung: "vorwaerts", "rueckwaerts", "links" oder "rechts"
        tempo:    0 (langsam) bis 100 (schnell)
        """
        namen = {"vorwaerts": "forward", "vorwärts": "forward", "rueckwaerts": "backward",
                 "rückwärts": "backward", "links": "left", "rechts": "right"}
        await self._befehl(f'motion.start_moving("{waehle(richtung, namen, "die Richtung")}", {tempo})',
                     "fahrt_start")

    async def stoppe(self) -> None:
        """Hält den Roboter an."""
        await self._befehl("motion.stop_moving()", "fahrt_stopp")

    async def raeder(self, links: int, rechts: int) -> None:
        """Steuert beide Räder einzeln: -100 (zurück) bis 100 (vor). 0 hält ein Rad an."""
        await self._befehl(f'motion.motor_pwm("L", {-links})', "motor_tempo")
        await self._befehl(f'motion.motor_pwm("R", {rechts})', "motor_tempo")

    # ------------------------------------------------------------ Licht (die 6 bunten LEDs)
    async def licht(self, farbe: Farbe) -> None:
        """Alle sechs Lichter in einer Farbe, z. B. licht("rot") oder licht((255, 0, 128))."""
        r, g, b = farbe_umrechnen(farbe)
        await self._befehl(f"leds.show_all({r}, {g}, {b})", "led_alle")

    async def licht_einzeln(self, position: Position, farbe: Farbe) -> None:
        """Ein einzelnes Licht in einer Farbe, z. B. licht_einzeln("links oben", "rot").

        Positionen (von vorne gesehen):

            links oben     rechts oben
            links mitte    rechts mitte
            links unten    rechts unten
        """
        nummer = waehle(position, POSITIONEN, "die Position")
        r, g, b = farbe_umrechnen(farbe)
        await self._befehl(f"leds.show_single({nummer}, {r}, {g}, {b})", "led_einzeln")

    async def lichter(self, farben: Mapping[Position, Farbe]) -> None:
        """Mehrere Lichter auf einmal, jedes mit eigener Farbe. Nicht genannte Lichter gehen aus.

            roboter.lichter({
                "links oben": "rot", "rechts oben": "gruen",
                "links unten": "blau", "rechts unten": "gelb",
            })

        Positionen: links oben, links mitte, links unten, rechts oben, rechts mitte, rechts unten
        """
        werte: dict[int, tuple[int, int, int]] = {}
        for position, farbe in farben.items():
            werte[waehle(position, POSITIONEN, "die Position")] = farbe_umrechnen(farbe)
        liste = [wert for nummer in range(1, 7) for wert in werte.get(nummer, (0, 0, 0))]
        await self._befehl(f"leds.display({liste})", "led_feld")

    async def licht_aus(self) -> None:
        """Schaltet alle Lichter aus."""
        await self._befehl("leds.show_all(0, 0, 0)", "led_aus")

    # ------------------------------------------------------------ Anzeige vorne (Punkte-Display)
    async def schreibe(self, text: str) -> None:
        """Schreibt einen Text als Laufschrift auf das Display (Umlaute werden evtl. nicht gezeigt)."""
        await self._befehl(f"led_matrix.write({text_literal(text)})", "text", 40)

    async def zeige_bild(self, zeilen: Sequence[str]) -> None:
        """Zeigt ein Bild, das du mit Zeichen malst: 8 Zeilen mit je 16 Zeichen.
        '#' leuchtet, alles andere bleibt dunkel.

            roboter.zeige_bild([
                "................",
                "...##......##...",
                "..####....####..",
                "..############..",
                "...##########...",
                "....########....",
                ".....######.....",
                "......####......",
            ])
        """
        daten = self._bild_daten(zeilen)
        await self._befehl(f'led_matrix.show_image(bytearray({daten}), "None")', "bild")

    async def zeige_pixel(self, spalte: int, zeile: int, helligkeit: int = 100) -> None:
        """Lässt einen einzelnen Punkt leuchten (spalte 0-15, zeile 0-7, helligkeit 0-100)."""
        await self._befehl(f"led_matrix.set_pixel({spalte}, {zeile}, {helligkeit})", "pixel")

    async def display_helligkeit(self, prozent: int) -> None:
        """Stellt die Helligkeit des Displays ein (0 bis 100)."""
        await self._befehl(f"led_matrix.set_brightness({prozent})", "helligkeit")

    async def display_aus(self) -> None:
        """Löscht das Display."""
        await self._befehl("led_matrix.clear()", "anzeige_aus")

    # ------------------------------------------------------------ Gefühle, Tänze, Bewegungen
    async def gefuehl(self, name: Gefuehl) -> None:
        """Der Roboter zeigt ein Gefühl (Gesicht, Ton und Bewegung).

        Mögliche Gefühle: froehlich, wuetend, traurig, ueberrascht, aengstlich, angeekelt,
        begeistert, schwindelig, muede, schlaefrig, wach, stolz
        """
        await self._befehl(f"action.emotion('{waehle(name, GEFUEHLE, 'das Gefühl')}')", "emotion", 40)

    async def tanze(self, name: Tanz) -> None:
        """Der Roboter tanzt. Mögliche Tänze: tango, walzer, steppen, samba, polonaise, jazz,
        rock, polka"""
        await self._befehl(f"action.dance('{waehle(name, TAENZE, 'den Tanz')}')", "tanz", 90)

    async def bewege_dich(self, name: Bewegung) -> None:
        """Der Roboter macht eine Bewegung. Mögliche Bewegungen: umschauen, verletzt,
        sprinten, kreisen, schuetteln"""
        await self._befehl(f"action.behavior('{waehle(name, BEWEGUNGEN, 'die Bewegung')}')",
                     "verhalten", 60)

    # ------------------------------------------------------------ Töne und Musik
    async def geraeusch(self, name: Geraeusch, warten: bool = True) -> None:
        """Spielt ein Geräusch ab. Mögliche Geräusche: krankenwagen, polizei, feuerwehr, zug,
        zugpfeife, schiffshorn, flugzeug, auto, automotor, magnetbahn"""
        await self._befehl(f"audio.effect('{waehle(name, GERAEUSCHE, 'das Geräusch')}', {warten})",
                     "effekt", 90 if warten else 15)

    async def lied(self, name: Lied, warten: bool = True) -> None:
        """Spielt ein Lied ab. Mögliche Lieder: funkel, jingle bells, geburtstag, freude,
        holzsoldaten, jagdpolka"""
        await self._befehl(f"audio.sing('{waehle(name, LIEDER, 'das Lied')}', {warten})", "lied",
                           240 if warten else 15)

    async def sprich(self, text: str, warten: bool = True) -> None:
        """Der Roboter spricht – aber nur Englisch (Wörter, Zahlen und Punkte)."""
        await self._befehl(f"audio.say({text_literal(text)}, {warten})", "sprich", 60 if warten else 15)

    async def ton(self, note: Note = "c", schlaege: float = 1, oktave: int = 4) -> None:
        """Spielt einen Ton. note: c d e f g a h (h ist das deutsche 'b'); schlaege: Länge;
        oktave: 3 tiefer, 4 normal, 5 höher."""
        grundton = waehle(note, NOTEN, "die Note")
        frequenz = round(grundton * math.pow(2.0, oktave - 4))
        await self._befehl(f"audio.play_tone({frequenz}, {schlaege})", "note", 60)

    async def ton_hoehe(self, midi_nummer: int, schlaege: float = 1) -> None:
        """Spielt einen Ton nach MIDI-Notennummer (60 = mittleres C, 69 = Kammerton a)."""
        frequenz = round(440.0 * math.pow(2.0, (midi_nummer - 69) / 12))
        await self._befehl(f"audio.play_tone({frequenz}, {schlaege})", "note", 60)

    async def pause(self, schlaege: float = 1) -> None:
        """Eine Pause in der Musik."""
        await self._befehl(f"audio.rest({schlaege})", "pause", 60)

    async def instrument(self, name: Instrument) -> None:
        """Wählt das Instrument für `ton()`, z. B. "klavier", "gitarre", "floete", "spieluhr"."""
        schluessel = str(name).lower().strip()
        if schluessel not in INSTRUMENTE:
            raise RoboterFehler(f"Das Instrument '{name}' kenne ich nicht. Mögliche: "
                                + ", ".join(INSTRUMENTE))
        await self._befehl(f"audio.set_instrument('{INSTRUMENTE.index(schluessel) + 1}')", "instrument")

    async def tempo(self, geschwindigkeit: int) -> None:
        """Wie schnell gespielt wird (große Zahl = schnell)."""
        await self._befehl(f"audio.set_tempo({geschwindigkeit})", "tempo")

    async def lautstaerke(self, prozent: int | None = None) -> int | None:
        """Ohne Zahl: gibt die Lautstärke zurück. Mit Zahl (0 bis 100): stellt sie ein."""
        if prozent is None:
            return await self._ganzzahl("audio.get_volume()")
        await self._befehl(f"audio.set_volume({prozent})", "lautstaerke")

    async def ton_stopp(self) -> None:
        """Beendet die Musik oder das Geräusch."""
        await self._befehl("audio.play_stop()", "ton_stopp")

    # ------------------------------------------------------------ Sensoren (messen)
    async def abstand(self) -> float | None:
        """Wie weit ist das nächste Hindernis vorne entfernt? (in Zentimetern)"""
        return await self._zahl("sensor.get_obstacle_avoidance_value()")

    async def helligkeit(self, seite: Seite = "links") -> float | None:
        """Wie hell ist es? seite: "links" oder "rechts"; Ergebnis in Prozent."""
        name = waehle(seite, {"links": "left", "rechts": "right"}, "die Seite")
        return await self._zahl(f"sensor.get_brightness('{name}')")

    async def untergrund(self, nummer: Bodensensor) -> int | None:
        """Wie hell ist der Boden unter dem Sensor 1 bis 5? 0 = dunkel (Linie), 100 = hell."""
        if not 1 <= nummer <= 5:
            raise RoboterFehler("Die Bodensensoren sind von 1 bis 5 nummeriert.")
        return await self._ganzzahl(f"sensor.get_reflection_light({nummer})")

    async def lautstaerke_umgebung(self) -> int | None:
        """Wie laut ist es um den Roboter herum?"""
        return await self._ganzzahl("sensor.loudness()")

    async def taste_gedrueckt(self, taste: Taste) -> bool | None:
        """Wird eine Taste des Roboters gerade gedrückt? taste: "dreieck", "quadrat" oder "kreis"."""
        namen = {"dreieck": "triangle", "quadrat": "square", "kreis": "circular"}
        return await self._wahrheit(f"button.is_pressed('{waehle(taste, namen, 'die Taste')}')")

    async def sieht_farbe(self, farbe: SensorFarbe) -> bool | None:
        """Sieht der Farbsensor unten diese Farbe? Antwort: True oder False.
        Farben: weiss, rot, gelb, gruen, blau, lila, schwarz"""
        return await self._wahrheit(f"sensor.is_color_detected('{waehle(farbe, FARBEN_SENSOR, 'die Farbe')}')")

    async def hindernis_naeher_als(self, zentimeter: float) -> bool | None:
        """Ist ein Hindernis näher als die angegebene Entfernung? True oder False."""
        return await self._wahrheit(f"sensor.is_obstacle_distance('<', {zentimeter})")

    async def sensorwerte(self) -> Sensorwerte | None:
        """Alle Sensorwerte auf einmal (aktueller Stand) als Wörterbuch."""
        return None if self._verbindung.sensoren is None else self._verbindung.sensoren.copy()

    # ------------------------------------------------------------ Infrarot
    async def sende_infrarot(self, text: str) -> None:
        """Schickt eine Nachricht per Infrarot an einen anderen Roboter."""
        await self._befehl(f"sensor.send_ir_message({text_literal(text)})", "ir_senden")

    async def empfange_infrarot(self) -> str | None:
        """Die zuletzt empfangene Infrarot-Nachricht (oder leer)."""
        return await self._text("sensor.get_ir_message()")

    # ------------------------------------------------------------ Erweitert: Fahren
    async def strecke_mit_tempo(self, millimeter: float, tempo: int = 50, warten: bool = True) -> None:
        """Fährt eine Strecke in Millimetern mit einstellbarem Tempo (0-100).
        Negative Zahlen fahren rückwärts. Mit warten=False geht das Programm sofort weiter."""
        await self._befehl(f"motion.move_raw_position({millimeter}, {tempo}, {warten})",
                           "strecke_tempo", 60)

    async def drehe_mit_tempo(self, grad: float, tempo: int = 50, warten: bool = True) -> None:
        """Dreht um einen Winkel mit einstellbarem Tempo. Positiv = links, negativ = rechts
        (so macht es auch die Scratch-Oberfläche des Herstellers)."""
        await self._befehl(f"motion.move_raw_angle({grad}, {tempo}, {warten})", "winkel_tempo", 60)

    async def rad_drehen(self, rad: Rad, wert: float, einheit: Einheit = "grad", tempo: int = 50, richtung: Drehrichtung = "uhrzeigersinn") -> None:
        """Lässt ein Rad drehen. rad: "links", "rechts" oder "beide";
        einheit: "grad", "umdrehungen" oder "sekunden"; richtung: "uhrzeigersinn" oder "gegen"."""
        raeder = {"links": "L", "rechts": "R", "beide": "L+R"}
        einheiten = {"grad": "degrees", "umdrehungen": "rotations", "sekunden": "seconds"}
        richtungen = {"uhrzeigersinn": "clockwise", "gegen": "counterclockwise"}
        rad_name = waehle(rad, raeder, "das Rad")
        einheit_name = waehle(einheit, einheiten, "die Einheit")
        richtung_name = waehle(richtung, richtungen, "die Richtung")
        await self._befehl(
            f'motion.motor_run("{rad_name}", {wert}, "{einheit_name}", {tempo}, "{richtung_name}")',
            "motor_lauf", 60)

    async def rad_stopp(self, rad: Rad = "beide") -> None:
        """Hält ein Rad an ("links", "rechts" oder "beide")."""
        raeder = {"links": "L", "rechts": "R", "beide": "L+R"}
        await self._befehl(f'motion.stop("{waehle(rad, raeder, "das Rad")}")', "motor_stopp")

    async def raddurchmesser(self, millimeter: float) -> None:
        """Stellt den Raddurchmesser ein (für genaueres Fahren)."""
        await self._befehl(f"motion.set_wheel_diameter({millimeter})", "abfrage")

    async def radabstand(self, millimeter: float) -> None:
        """Stellt den Abstand zwischen den Rädern ein (für genaueres Drehen)."""
        await self._befehl(f"motion.set_wheel_base({millimeter})", "abfrage")

    async def fahr_einstellungen_zuruecksetzen(self) -> None:
        """Setzt Raddurchmesser, Radabstand usw. auf die Werkseinstellung zurück."""
        await self._befehl("motion.reset_default_settings()", "abfrage")

    # ------------------------------------------------------------ Erweitert: Display
    async def zeige_bild_fuer(self, zeilen: Sequence[str], sekunden: float) -> None:
        """Wie `zeige_bild`, aber nur für einige Sekunden."""
        daten = self._bild_daten(zeilen)
        await self._befehl(f"led_matrix.show_image(bytearray({daten}), {sekunden})", "bild", 60)

    @staticmethod
    def _bild_daten(zeilen: Sequence[str]) -> list[int]:
        zeilen = list(zeilen)
        if len(zeilen) != 8 or any(len(z) != 16 for z in zeilen):
            raise RoboterFehler("Das Bild braucht genau 8 Zeilen mit je 16 Zeichen.")
        # Wie die Hersteller-Oberfläche: Das erste Pixel einer 8er-Gruppe ist das niedrigste Bit.
        return [sum(1 << i for i, z in enumerate(h) if z == "#")
                for zeile in zeilen for h in (zeile[:8], zeile[8:])]

    async def display_richtung(self, richtung: DisplayRichtung) -> None:
        """In welche Richtung die Laufschrift wandert: "hoch", "runter", "links", "rechts"."""
        namen = {"hoch": "up", "runter": "down", "links": "left", "rechts": "right"}
        await self._befehl(f'led_matrix.set_orientation("{waehle(richtung, namen, "die Richtung")}")',
                           "ausrichtung")

    async def display_drehen(self, richtung: Drehrichtung = "uhrzeigersinn") -> None:
        """Dreht das Bild auf dem Display: "uhrzeigersinn" oder "gegen"."""
        namen = {"uhrzeigersinn": "clockwise", "gegen": "counterclockwise"}
        await self._befehl(f'led_matrix.screen_rotate("{waehle(richtung, namen, "die Richtung")}")',
                           "anzeige_drehen")

    # ------------------------------------------------------------ Erweitert: Ton
    async def trommel(self, name: str, schlaege: float = 1) -> None:
        """Spielt eine Trommel (Namen vom Hersteller nicht dokumentiert, z. B. "snare")."""
        await self._befehl(f"audio.play_drums('{name}', {schlaege})", "trommel", 60)

    async def spiele_datei(self, pfad: str, warten: bool = True) -> None:
        """Spielt eine Ton-Datei ab (mp3, wav oder amr), die auf dem Roboter liegt,
        z. B. "/sdcard/music/effect/24-aircraft.mp3"."""
        await self._befehl(f"audio.play({text_literal(pfad)}, {warten})", "datei", 240)

    async def lautstaerke_aendern(self, aenderung: int) -> None:
        """Macht den Roboter lauter (positive Zahl) oder leiser (negative Zahl)."""
        await self._befehl(f"audio.set_volume(audio.get_volume() + {aenderung})", "lautstaerke")

    async def tempo_aendern(self, aenderung: float) -> None:
        """Erhöht (positive Zahl) oder senkt (negative Zahl) das Spieltempo."""
        await self._befehl(f"audio.set_tempo(audio.get_tempo() + {aenderung})", "tempo")

    async def aktuelles_tempo(self) -> float | None:
        """Gibt das aktuelle Spieltempo der Musik zurück."""
        return await self._zahl("audio.get_tempo()")

    # ------------------------------------------------------------ Erweitert: Sensoren
    async def linie_erkannt(self, nummer: Bodensensor, farbe: Linienfarbe = "schwarz") -> bool | None:
        """Sieht Bodensensor 1-5 gerade "schwarz" oder "weiss"? True oder False."""
        wert = waehle(farbe, {"weiss": 0, "weiß": 0, "schwarz": 1}, "die Farbe")
        return await self._wahrheit(f"sensor.is_line_following_sensor_detected({nummer}, {wert})")

    async def farbwert(self, kanal: Farbkanal) -> int | None:
        """Wie viel Rot, Grün oder Blau sieht der Farbsensor? kanal: "rot", "gruen", "blau"."""
        namen = {"rot": "red", "gruen": "green", "grün": "green", "blau": "blue"}
        return await self._ganzzahl(f"sensor.get_color_channel('{waehle(kanal, namen, 'den Kanal')}')")

    async def farbsensor_kalibrieren(self) -> None:
        """Eicht den Farbsensor. Vorher den Roboter auf eine weiße Fläche stellen."""
        await self._befehl("sensor.color_calibration()", "abfrage", 20)

    async def infrarot_angekommen(self, text: str) -> bool | None:
        """Wurde genau diese Infrarot-Nachricht empfangen? True oder False."""
        return await self._wahrheit(f"sensor.is_ir_message_received({text_literal(text)})")

    async def fernbedienung(self, taste: Fernbedienungstaste) -> bool | None:
        """Wurde diese Taste der Infrarot-Fernbedienung gedrückt? Tasten: volume, mode, speed,
        forward, backward, left, right, play, dance, led, music, 1, 2, 3"""
        return await self._wahrheit(f"sensor.is_ir_code_received('{taste}')")

    # ------------------------------------------------------------ Erweitert: Warten auf Sensoren
    async def warte_bis(self, bedingung: Callable[[Sensorwerte], bool], zeitlimit: float = 30) -> bool:
        """Wartet, bis `bedingung(sensorwerte)` wahr ist. Gibt True zurück, sonst nach
        dem Zeitlimit False.

            await roboter.warte_bis(lambda werte: werte["abstand_cm"] < 10)
        """
        schleife = asyncio.get_running_loop()
        ende = schleife.time() + zeitlimit
        while schleife.time() < ende:
            werte = self._verbindung.sensoren
            if werte is not None and bedingung(werte.copy()):
                return True
            await asyncio.sleep(0.05)
        return False

    async def sensorstrom(self, intervall: float = 0.2) -> AsyncIterator[Sensorwerte]:
        """Liefert fortlaufend die aktuellen Sensorwerte:

            async for werte in roboter.sensorstrom():
                print(werte["abstand_cm"])
        """
        while True:
            werte = self._verbindung.sensoren
            if werte is not None:
                yield werte.copy()
            await asyncio.sleep(intervall)

    # ------------------------------------------------------------ Für Fortgeschrittene
    async def firmware_version(self) -> str | None:
        """Die Firmware-Version des Roboters als Text, z. B. "1.2.0"."""
        return await self._verbindung.firmware_abfragen()

    async def roh(self, befehl: str, zeitlimit: float = 15) -> str | None:
        """Führt beliebigen MicroPython-Code des Roboters aus (siehe docs/firmware-api/) und gibt
        die Antwort als Text zurück. Beispiel: `await roboter.roh("motion.stop_moving()")`."""
        antwort = await self._antwort(befehl, "abfrage", zeitlimit)
        return None if antwort is None else antwort.text
