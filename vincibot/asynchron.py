"""Die volle Schnittstelle zum VinciBot mit `async`/`await`.

Damit kann der Roboter mehrere Dinge gleichzeitig tun, zum Beispiel fahren und dabei blinken.
Für den Einstieg ist die einfachere Klasse `VinciBot` (ohne async) gedacht.

Beispiel:
    import asyncio
    from vincibot import VinciBotAsync

    async def haupt():
        async with VinciBotAsync() as roboter:
            await asyncio.gather(roboter.vorwaerts(20), roboter.lichter(["rot"] * 6))

    asyncio.run(haupt())
"""
import asyncio

from . import _protokoll as p
from ._verbindung import Verbindung
from ._woerter import (BEWEGUNGEN, FARBEN_SENSOR, GEFUEHLE, GERAEUSCHE, INSTRUMENTE, LIEDER,
                       NOTEN, TAENZE, RoboterFehler, _farbe, _waehle)


class VinciBotAsync:
    """Dein Roboter – mit `await` bedienen. Alle Methoden sind `async`."""

    def __init__(self, adresse=None, suchdauer=15):
        """adresse: nur nötig, wenn mehrere Roboter in der Nähe sind (z. B. "AA:BB:CC:DD:EE:FF").
        suchdauer: Wie viele Sekunden nach dem Roboter gesucht wird."""
        self._verbindung = Verbindung(adresse=adresse, suchdauer=suchdauer)

    # ------------------------------------------------------------ Verbindung
    async def verbinden(self):
        """Verbindet sich mit dem Roboter (macht `async with` automatisch)."""
        await self._verbindung.verbinden()

    async def trennen(self):
        """Beendet die Verbindung zum Roboter."""
        await self._verbindung.trennen()

    async def __aenter__(self):
        await self.verbinden()
        return self

    async def __aexit__(self, *_):
        await self.trennen()

    # ------------------------------------------------------------ Hilfsmittel (intern)
    async def _befehl(self, code, art, wartezeit=15):
        antwort = await self._verbindung.befehl(code, p.SEQUENZ[art], wartezeit)
        if antwort is not None and antwort.fehler:
            raise RoboterFehler(f"Der Roboter konnte das nicht ausführen ({antwort.text}).")
        return antwort

    async def _frage(self, ausdruck):
        antwort = await self._befehl(ausdruck, "abfrage", 5)
        if antwort is None:
            return None
        text = antwort.text.strip()
        if text in ("True", "False"):
            return text == "True"
        for typ in (int, float):
            try:
                return typ(text)
            except ValueError:
                pass
        return text

    async def warte(self, sekunden):
        """Wartet, ohne etwas zu tun."""
        await asyncio.sleep(sekunden)

    # ------------------------------------------------------------ Fahren
    async def vorwaerts(self, zentimeter=10):
        """Fährt die angegebene Strecke nach vorne."""
        await self._befehl(f'motion.move_position("forward", {zentimeter}, "cm")', "strecke", 30)

    async def rueckwaerts(self, zentimeter=10):
        """Fährt die angegebene Strecke rückwärts."""
        await self._befehl(f'motion.move_position("backward", {zentimeter}, "cm")', "strecke", 30)

    async def links(self, grad=90):
        """Dreht sich auf der Stelle nach links."""
        await self._befehl(f'motion.move_angle("left", {grad}, "degrees")', "winkel", 30)

    async def rechts(self, grad=90):
        """Dreht sich auf der Stelle nach rechts."""
        await self._befehl(f'motion.move_angle("right", {grad}, "degrees")', "winkel", 30)

    async def fahre(self, richtung="vorwaerts", tempo=50):
        """Fährt immer weiter, bis du `stoppe()` aufrufst.

        richtung: "vorwaerts", "rueckwaerts", "links" oder "rechts"
        tempo:    0 (langsam) bis 100 (schnell)
        """
        namen = {"vorwaerts": "forward", "vorwärts": "forward", "rueckwaerts": "backward",
                 "rückwärts": "backward", "links": "left", "rechts": "right"}
        await self._befehl(f'motion.start_moving("{_waehle(richtung, namen, "die Richtung")}", {tempo})',
                     "fahrt_start")

    async def stoppe(self):
        """Hält den Roboter an."""
        await self._befehl("motion.stop_moving()", "fahrt_stopp")

    async def raeder(self, links, rechts):
        """Steuert beide Räder einzeln: -100 (zurück) bis 100 (vor). 0 hält ein Rad an."""
        await self._befehl(f'motion.motor_pwm("L", {-links})', "motor_tempo")
        await self._befehl(f'motion.motor_pwm("R", {rechts})', "motor_tempo")

    # ------------------------------------------------------------ Licht (die 6 bunten LEDs)
    async def licht(self, farbe):
        """Alle sechs Lichter in einer Farbe, z. B. licht("rot") oder licht((255, 0, 128))."""
        r, g, b = _farbe(farbe)
        await self._befehl(f"leds.show_all({r}, {g}, {b})", "led_alle")

    async def licht_einzeln(self, nummer, farbe):
        """Ein einzelnes Licht (Nummer 1 bis 6) in einer Farbe."""
        if not 1 <= nummer <= 6:
            raise RoboterFehler("Die Lichter sind von 1 bis 6 nummeriert.")
        r, g, b = _farbe(farbe)
        await self._befehl(f"leds.show_single({nummer}, {r}, {g}, {b})", "led_einzeln")

    async def lichter(self, farben):
        """Alle sechs Lichter einzeln, z. B. lichter(["rot", "gelb", "gruen", "blau", "lila", "weiss"])."""
        farben = list(farben)
        if len(farben) != 6:
            raise RoboterFehler("Gib genau sechs Farben an – eine für jedes Licht.")
        werte = [wert for farbe in farben for wert in _farbe(farbe)]
        await self._befehl(f"leds.display({werte})", "led_feld")

    async def licht_aus(self):
        """Schaltet alle Lichter aus."""
        await self._befehl("leds.show_all(0, 0, 0)", "led_aus")

    # ------------------------------------------------------------ Anzeige vorne (Punkte-Display)
    async def schreibe(self, text):
        """Schreibt einen Text als Laufschrift auf das Display (Umlaute werden evtl. nicht gezeigt)."""
        await self._befehl(f"led_matrix.write({p.text_literal(text)})", "text", 40)

    async def zeige_bild(self, zeilen):
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

    async def zeige_pixel(self, spalte, zeile, helligkeit=100):
        """Lässt einen einzelnen Punkt leuchten (spalte 0-15, zeile 0-7, helligkeit 0-100)."""
        await self._befehl(f"led_matrix.set_pixel({spalte}, {zeile}, {helligkeit})", "pixel")

    async def display_helligkeit(self, prozent):
        """Stellt die Helligkeit des Displays ein (0 bis 100)."""
        await self._befehl(f"led_matrix.set_brightness({prozent})", "helligkeit")

    async def display_aus(self):
        """Löscht das Display."""
        await self._befehl("led_matrix.clear()", "anzeige_aus")

    # ------------------------------------------------------------ Gefühle, Tänze, Bewegungen
    async def gefuehl(self, name):
        """Der Roboter zeigt ein Gefühl (Gesicht, Ton und Bewegung).

        Mögliche Gefühle: froehlich, wuetend, traurig, ueberrascht, aengstlich, angeekelt,
        begeistert, schwindelig, muede, schlaefrig, wach, stolz
        """
        await self._befehl(f"action.emotion('{_waehle(name, GEFUEHLE, 'das Gefühl')}')", "emotion", 40)

    async def tanze(self, name):
        """Der Roboter tanzt. Mögliche Tänze: tango, walzer, steppen, samba, polonaise, jazz,
        rock, polka"""
        await self._befehl(f"action.dance('{_waehle(name, TAENZE, 'den Tanz')}')", "tanz", 90)

    async def bewege_dich(self, name):
        """Der Roboter macht eine Bewegung. Mögliche Bewegungen: umschauen, verletzt,
        sprinten, kreisen, schuetteln"""
        await self._befehl(f"action.behavior('{_waehle(name, BEWEGUNGEN, 'die Bewegung')}')",
                     "verhalten", 60)

    # ------------------------------------------------------------ Töne und Musik
    async def geraeusch(self, name):
        """Spielt ein Geräusch ab. Mögliche Geräusche: krankenwagen, polizei, feuerwehr, zug,
        zugpfeife, schiffshorn, flugzeug, auto, automotor, magnetbahn"""
        await self._befehl(f"audio.effect('{_waehle(name, GERAEUSCHE, 'das Geräusch')}', True)",
                     "effekt", 90)

    async def lied(self, name):
        """Spielt ein Lied ab. Mögliche Lieder: funkel, jingle bells, geburtstag, freude,
        holzsoldaten, jagdpolka"""
        await self._befehl(f"audio.sing('{_waehle(name, LIEDER, 'das Lied')}', True)", "lied", 240)

    async def sprich(self, text):
        """Der Roboter spricht – aber nur Englisch (Wörter, Zahlen und Punkte)."""
        await self._befehl(f"audio.say({p.text_literal(text)}, True)", "sprich", 60)

    async def ton(self, note="c", schlaege=1, oktave=4):
        """Spielt einen Ton. note: c d e f g a h (h ist das deutsche 'b'); schlaege: Länge;
        oktave: 3 tiefer, 4 normal, 5 höher."""
        grundton = _waehle(note, NOTEN, "die Note")
        frequenz = round(grundton * 2 ** (oktave - 4))
        await self._befehl(f"audio.play_tone({frequenz}, {schlaege})", "note", 60)

    async def pause(self, schlaege=1):
        """Eine Pause in der Musik."""
        await self._befehl(f"audio.rest({schlaege})", "pause", 60)

    async def instrument(self, name):
        """Wählt das Instrument für `ton()`, z. B. "klavier", "gitarre", "floete", "spieluhr"."""
        schluessel = str(name).lower().strip()
        if schluessel not in INSTRUMENTE:
            raise RoboterFehler(f"Das Instrument '{name}' kenne ich nicht. Mögliche: "
                                + ", ".join(INSTRUMENTE))
        await self._befehl(f"audio.set_instrument('{INSTRUMENTE.index(schluessel) + 1}')", "instrument")

    async def tempo(self, geschwindigkeit):
        """Wie schnell gespielt wird (große Zahl = schnell)."""
        await self._befehl(f"audio.set_tempo({geschwindigkeit})", "tempo")

    async def lautstaerke(self, prozent=None):
        """Ohne Zahl: gibt die Lautstärke zurück. Mit Zahl (0 bis 100): stellt sie ein."""
        if prozent is None:
            return await self._frage("audio.get_volume()")
        await self._befehl(f"audio.set_volume({prozent})", "lautstaerke")

    async def ton_stopp(self):
        """Beendet die Musik oder das Geräusch."""
        await self._befehl("audio.play_stop()", "ton_stopp")

    # ------------------------------------------------------------ Sensoren (messen)
    async def abstand(self):
        """Wie weit ist das nächste Hindernis vorne entfernt? (in Zentimetern)"""
        return await self._frage("sensor.get_obstacle_avoidance_value()")

    async def helligkeit(self, seite="links"):
        """Wie hell ist es? seite: "links" oder "rechts"; Ergebnis in Prozent."""
        name = _waehle(seite, {"links": "left", "rechts": "right"}, "die Seite")
        return await self._frage(f"sensor.get_brightness('{name}')")

    async def untergrund(self, nummer):
        """Wie hell ist der Boden unter dem Sensor 1 bis 5? 0 = dunkel (Linie), 100 = hell."""
        if not 1 <= nummer <= 5:
            raise RoboterFehler("Die Bodensensoren sind von 1 bis 5 nummeriert.")
        return await self._frage(f"sensor.get_reflection_light({nummer})")

    async def lautstaerke_umgebung(self):
        """Wie laut ist es um den Roboter herum?"""
        return await self._frage("sensor.loudness()")

    async def sieht_farbe(self, farbe):
        """Sieht der Farbsensor unten diese Farbe? Antwort: True oder False.
        Farben: weiss, rot, gelb, gruen, blau, lila, schwarz"""
        return await self._frage(f"sensor.is_color_detected('{_waehle(farbe, FARBEN_SENSOR, 'die Farbe')}')")

    async def hindernis_naeher_als(self, zentimeter):
        """Ist ein Hindernis näher als die angegebene Entfernung? True oder False."""
        return await self._frage(f"sensor.is_obstacle_distance('<', {zentimeter})")

    async def sensorwerte(self):
        """Alle Sensorwerte auf einmal (aktueller Stand) als Wörterbuch."""
        return dict(self._verbindung.sensoren)

    # ------------------------------------------------------------ Infrarot
    async def sende_infrarot(self, text):
        """Schickt eine Nachricht per Infrarot an einen anderen Roboter."""
        await self._befehl(f"sensor.send_ir_message({p.text_literal(text)})", "ir_senden")

    async def empfange_infrarot(self):
        """Die zuletzt empfangene Infrarot-Nachricht (oder leer)."""
        return await self._frage("sensor.get_ir_message()")

    # ------------------------------------------------------------ Erweitert: Fahren
    async def strecke_mit_tempo(self, millimeter, tempo=50, warten=True):
        """Fährt eine Strecke in Millimetern mit einstellbarem Tempo (0-100).
        Negative Zahlen fahren rückwärts. Mit warten=False geht das Programm sofort weiter."""
        await self._befehl(f"motion.move_raw_position({millimeter}, {tempo}, {warten})",
                           "strecke_tempo", 60)

    async def drehe_mit_tempo(self, grad, tempo=50, warten=True):
        """Dreht um einen Winkel mit einstellbarem Tempo. Positiv = rechts, negativ = links."""
        await self._befehl(f"motion.move_raw_angle({grad}, {tempo}, {warten})", "winkel_tempo", 60)

    async def rad_drehen(self, rad, wert, einheit="grad", tempo=50, richtung="uhrzeigersinn"):
        """Lässt ein Rad drehen. rad: "links", "rechts" oder "beide";
        einheit: "grad", "umdrehungen" oder "sekunden"; richtung: "uhrzeigersinn" oder "gegen"."""
        raeder = {"links": "L", "rechts": "R", "beide": "L+R"}
        einheiten = {"grad": "degrees", "umdrehungen": "rotations", "sekunden": "seconds"}
        richtungen = {"uhrzeigersinn": "clockwise", "gegen": "counterclockwise"}
        await self._befehl(
            f'motion.motor_run("{_waehle(rad, raeder, "das Rad")}", {wert}, '
            f'"{_waehle(einheit, einheiten, "die Einheit")}", {tempo}, '
            f'"{_waehle(richtung, richtungen, "die Richtung")}")', "motor_lauf", 60)

    async def rad_stopp(self, rad="beide"):
        """Hält ein Rad an ("links", "rechts" oder "beide")."""
        raeder = {"links": "L", "rechts": "R", "beide": "L+R"}
        await self._befehl(f'motion.stop("{_waehle(rad, raeder, "das Rad")}")', "motor_stopp")

    async def raddurchmesser(self, millimeter):
        """Stellt den Raddurchmesser ein (für genaueres Fahren)."""
        await self._befehl(f"motion.set_wheel_diameter({millimeter})", "abfrage")

    async def radabstand(self, millimeter):
        """Stellt den Abstand zwischen den Rädern ein (für genaueres Drehen)."""
        await self._befehl(f"motion.set_wheel_base({millimeter})", "abfrage")

    async def fahr_einstellungen_zuruecksetzen(self):
        """Setzt Raddurchmesser, Radabstand usw. auf die Werkseinstellung zurück."""
        await self._befehl("motion.reset_default_settings()", "abfrage")

    # ------------------------------------------------------------ Erweitert: Display
    async def zeige_bild_fuer(self, zeilen, sekunden):
        """Wie `zeige_bild`, aber nur für einige Sekunden."""
        daten = self._bild_daten(zeilen)
        await self._befehl(f"led_matrix.show_image(bytearray({daten}), {sekunden})", "bild", 60)

    @staticmethod
    def _bild_daten(zeilen):
        zeilen = list(zeilen)
        if len(zeilen) != 8 or any(len(z) != 16 for z in zeilen):
            raise RoboterFehler("Das Bild braucht genau 8 Zeilen mit je 16 Zeichen.")
        return [sum(1 << (7 - i) for i, z in enumerate(h) if z == "#")
                for zeile in zeilen for h in (zeile[:8], zeile[8:])]

    async def display_richtung(self, richtung):
        """In welche Richtung die Laufschrift wandert: "hoch", "runter", "links", "rechts"."""
        namen = {"hoch": "up", "runter": "down", "links": "left", "rechts": "right"}
        await self._befehl(f'led_matrix.set_orientation("{_waehle(richtung, namen, "die Richtung")}")',
                           "ausrichtung")

    async def display_drehen(self, richtung="uhrzeigersinn"):
        """Dreht das Bild auf dem Display: "uhrzeigersinn" oder "gegen"."""
        namen = {"uhrzeigersinn": "clockwise", "gegen": "counterclockwise"}
        await self._befehl(f'led_matrix.screen_rotate("{_waehle(richtung, namen, "die Richtung")}")',
                           "anzeige_drehen")

    # ------------------------------------------------------------ Erweitert: Ton
    async def trommel(self, name, schlaege=1):
        """Spielt eine Trommel (Namen vom Hersteller nicht dokumentiert, z. B. "snare")."""
        await self._befehl(f"audio.play_drums('{name}', {schlaege})", "trommel", 60)

    async def spiele_datei(self, pfad, warten=True):
        """Spielt eine Ton-Datei ab (mp3, wav oder amr), die auf dem Roboter liegt,
        z. B. "/sdcard/music/effect/24-aircraft.mp3"."""
        await self._befehl(f"audio.play({p.text_literal(pfad)}, {warten})", "datei", 240)

    async def lautstaerke_aendern(self, aenderung):
        """Macht den Roboter lauter (positive Zahl) oder leiser (negative Zahl)."""
        await self._befehl(f"audio.set_volume(audio.get_volume() + {aenderung})", "lautstaerke")

    async def aktuelles_tempo(self):
        """Gibt das aktuelle Spieltempo der Musik zurück."""
        return await self._frage("audio.get_tempo()")

    # ------------------------------------------------------------ Erweitert: Sensoren
    async def linie_erkannt(self, nummer, farbe="schwarz"):
        """Sieht Bodensensor 1-5 gerade "schwarz" oder "weiss"? True oder False."""
        wert = _waehle(farbe, {"weiss": 0, "weiß": 0, "schwarz": 1}, "die Farbe")
        return await self._frage(f"sensor.is_line_following_sensor_detected({nummer}, {wert})")

    async def farbwert(self, kanal):
        """Wie viel Rot, Grün oder Blau sieht der Farbsensor? kanal: "rot", "gruen", "blau"."""
        namen = {"rot": "red", "gruen": "green", "grün": "green", "blau": "blue"}
        return await self._frage(f"sensor.get_color_channel('{_waehle(kanal, namen, 'den Kanal')}')")

    async def farbsensor_kalibrieren(self):
        """Eicht den Farbsensor. Vorher den Roboter auf eine weiße Fläche stellen."""
        await self._befehl("sensor.color_calibration()", "abfrage", 20)

    async def infrarot_angekommen(self, text):
        """Wurde genau diese Infrarot-Nachricht empfangen? True oder False."""
        return await self._frage(f"sensor.is_ir_message_received({p.text_literal(text)})")

    async def fernbedienung(self, taste):
        """Wurde diese Taste der Infrarot-Fernbedienung gedrückt? Tasten: volume, mode, speed,
        forward, backward, left, right, play, dance, led, music, 1, 2, 3"""
        return await self._frage(f"sensor.is_ir_code_received('{taste}')")

    # ------------------------------------------------------------ Erweitert: Warten auf Sensoren
    async def warte_bis(self, bedingung, zeitlimit=30):
        """Wartet, bis `bedingung(sensorwerte)` wahr ist. Gibt True zurück, sonst nach
        dem Zeitlimit False.

            await roboter.warte_bis(lambda werte: werte["abstand_cm"] < 10)
        """
        ende = asyncio.get_event_loop().time() + zeitlimit
        while asyncio.get_event_loop().time() < ende:
            if self._verbindung.sensoren and bedingung(dict(self._verbindung.sensoren)):
                return True
            await asyncio.sleep(0.05)
        return False

    async def sensorstrom(self, intervall=0.2):
        """Liefert fortlaufend die aktuellen Sensorwerte:

            async for werte in roboter.sensorstrom():
                print(werte["abstand_cm"])
        """
        while True:
            if self._verbindung.sensoren:
                yield dict(self._verbindung.sensoren)
            await asyncio.sleep(intervall)

    # ------------------------------------------------------------ Für Fortgeschrittene
    async def roh(self, befehl, zeitlimit=15):
        """Führt beliebigen MicroPython-Code des Roboters aus (siehe docs/firmware-api/) und gibt
        die Antwort als Text zurück. Beispiel: `await roboter.roh("motion.stop_moving()")`."""
        antwort = await self._verbindung.befehl(befehl, p.SEQUENZ["abfrage"], zeitlimit)
        if antwort is None:
            return None
        if antwort.fehler:
            raise RoboterFehler(f"Der Roboter konnte das nicht ausführen ({antwort.text}).")
        return antwort.text
