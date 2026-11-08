"""Die einfache Schnittstelle zum VinciBot – gemacht zum Programmieren lernen (ohne async).

ACHTUNG: Diese Datei wird automatisch erzeugt (python werkzeuge/erzeuge_roboter.py).
Änderungen bitte in asynchron.py machen und die Datei neu erzeugen.
"""
import asyncio
import threading

from .asynchron import VinciBotAsync


class VinciBot:
    """Dein Roboter.

    Beispiel:
        from vincibot import VinciBot

        roboter = VinciBot()          # verbindet sich mit dem Roboter
        roboter.vorwaerts(10)         # 10 Zentimeter nach vorne
        roboter.rechts(90)            # nach rechts drehen
        roboter.licht("gruen")        # alle Lichter grün
        roboter.trennen()             # Verbindung beenden

    Noch kürzer, und die Verbindung wird automatisch beendet:
        with VinciBot() as roboter:
            roboter.vorwaerts(10)
    """

    def __init__(self, adresse=None, suchdauer=15):
        """Verbindet sich mit dem Roboter.

        adresse:   Nur nötig, wenn mehrere Roboter in der Nähe sind (z. B. "AA:BB:CC:DD:EE:FF").
        suchdauer: Wie viele Sekunden nach dem Roboter gesucht wird.
        """
        self._schleife = asyncio.new_event_loop()
        self._faden = threading.Thread(target=self._schleife.run_forever, daemon=True)
        self._faden.start()
        self._roboter = VinciBotAsync(adresse=adresse, suchdauer=suchdauer)
        try:
            self._laufen(self._roboter.verbinden())
        except BaseException:
            self._beende_schleife()
            raise

    def _laufen(self, aufgabe):
        return asyncio.run_coroutine_threadsafe(aufgabe, self._schleife).result()

    def _beende_schleife(self):
        self._schleife.call_soon_threadsafe(self._schleife.stop)
        self._faden.join(timeout=2)

    def trennen(self):
        """Beendet die Verbindung zum Roboter."""
        try:
            self._laufen(self._roboter.trennen())
        finally:
            self._beende_schleife()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.trennen()

    def abstand(self):
        """Wie weit ist das nächste Hindernis vorne entfernt? (in Zentimetern)
        """
        return self._laufen(self._roboter.abstand())

    def aktuelles_tempo(self):
        """Gibt das aktuelle Spieltempo der Musik zurück.
        """
        return self._laufen(self._roboter.aktuelles_tempo())

    def bewege_dich(self, name):
        """Der Roboter macht eine Bewegung. Mögliche Bewegungen: umschauen, verletzt,
        sprinten, kreisen, schuetteln
        """
        return self._laufen(self._roboter.bewege_dich(name))

    def display_aus(self):
        """Löscht das Display.
        """
        return self._laufen(self._roboter.display_aus())

    def display_drehen(self, richtung='uhrzeigersinn'):
        """Dreht das Bild auf dem Display: "uhrzeigersinn" oder "gegen".
        """
        return self._laufen(self._roboter.display_drehen(richtung))

    def display_helligkeit(self, prozent):
        """Stellt die Helligkeit des Displays ein (0 bis 100).
        """
        return self._laufen(self._roboter.display_helligkeit(prozent))

    def display_richtung(self, richtung):
        """In welche Richtung die Laufschrift wandert: "hoch", "runter", "links", "rechts".
        """
        return self._laufen(self._roboter.display_richtung(richtung))

    def drehe_mit_tempo(self, grad, tempo=50, warten=True):
        """Dreht um einen Winkel mit einstellbarem Tempo. Positiv = rechts, negativ = links.
        """
        return self._laufen(self._roboter.drehe_mit_tempo(grad, tempo, warten))

    def empfange_infrarot(self):
        """Die zuletzt empfangene Infrarot-Nachricht (oder leer).
        """
        return self._laufen(self._roboter.empfange_infrarot())

    def fahr_einstellungen_zuruecksetzen(self):
        """Setzt Raddurchmesser, Radabstand usw. auf die Werkseinstellung zurück.
        """
        return self._laufen(self._roboter.fahr_einstellungen_zuruecksetzen())

    def fahre(self, richtung='vorwaerts', tempo=50):
        """Fährt immer weiter, bis du `stoppe()` aufrufst.

        richtung: "vorwaerts", "rueckwaerts", "links" oder "rechts"
        tempo:    0 (langsam) bis 100 (schnell)
        """
        return self._laufen(self._roboter.fahre(richtung, tempo))

    def farbsensor_kalibrieren(self):
        """Eicht den Farbsensor. Vorher den Roboter auf eine weiße Fläche stellen.
        """
        return self._laufen(self._roboter.farbsensor_kalibrieren())

    def farbwert(self, kanal):
        """Wie viel Rot, Grün oder Blau sieht der Farbsensor? kanal: "rot", "gruen", "blau".
        """
        return self._laufen(self._roboter.farbwert(kanal))

    def fernbedienung(self, taste):
        """Wurde diese Taste der Infrarot-Fernbedienung gedrückt? Tasten: volume, mode, speed,
        forward, backward, left, right, play, dance, led, music, 1, 2, 3
        """
        return self._laufen(self._roboter.fernbedienung(taste))

    def gefuehl(self, name):
        """Der Roboter zeigt ein Gefühl (Gesicht, Ton und Bewegung).

        Mögliche Gefühle: froehlich, wuetend, traurig, ueberrascht, aengstlich, angeekelt,
        begeistert, schwindelig, muede, schlaefrig, wach, stolz
        """
        return self._laufen(self._roboter.gefuehl(name))

    def geraeusch(self, name):
        """Spielt ein Geräusch ab. Mögliche Geräusche: krankenwagen, polizei, feuerwehr, zug,
        zugpfeife, schiffshorn, flugzeug, auto, automotor, magnetbahn
        """
        return self._laufen(self._roboter.geraeusch(name))

    def helligkeit(self, seite='links'):
        """Wie hell ist es? seite: "links" oder "rechts"; Ergebnis in Prozent.
        """
        return self._laufen(self._roboter.helligkeit(seite))

    def hindernis_naeher_als(self, zentimeter):
        """Ist ein Hindernis näher als die angegebene Entfernung? True oder False.
        """
        return self._laufen(self._roboter.hindernis_naeher_als(zentimeter))

    def infrarot_angekommen(self, text):
        """Wurde genau diese Infrarot-Nachricht empfangen? True oder False.
        """
        return self._laufen(self._roboter.infrarot_angekommen(text))

    def instrument(self, name):
        """Wählt das Instrument für `ton()`, z. B. "klavier", "gitarre", "floete", "spieluhr".
        """
        return self._laufen(self._roboter.instrument(name))

    def lautstaerke(self, prozent=None):
        """Ohne Zahl: gibt die Lautstärke zurück. Mit Zahl (0 bis 100): stellt sie ein.
        """
        return self._laufen(self._roboter.lautstaerke(prozent))

    def lautstaerke_aendern(self, aenderung):
        """Macht den Roboter lauter (positive Zahl) oder leiser (negative Zahl).
        """
        return self._laufen(self._roboter.lautstaerke_aendern(aenderung))

    def lautstaerke_umgebung(self):
        """Wie laut ist es um den Roboter herum?
        """
        return self._laufen(self._roboter.lautstaerke_umgebung())

    def licht(self, farbe):
        """Alle sechs Lichter in einer Farbe, z. B. licht("rot") oder licht((255, 0, 128)).
        """
        return self._laufen(self._roboter.licht(farbe))

    def licht_aus(self):
        """Schaltet alle Lichter aus.
        """
        return self._laufen(self._roboter.licht_aus())

    def licht_einzeln(self, nummer, farbe):
        """Ein einzelnes Licht (Nummer 1 bis 6) in einer Farbe.
        """
        return self._laufen(self._roboter.licht_einzeln(nummer, farbe))

    def lichter(self, farben):
        """Alle sechs Lichter einzeln, z. B. lichter(["rot", "gelb", "gruen", "blau", "lila", "weiss"]).
        """
        return self._laufen(self._roboter.lichter(farben))

    def lied(self, name):
        """Spielt ein Lied ab. Mögliche Lieder: funkel, jingle bells, geburtstag, freude,
        holzsoldaten, jagdpolka
        """
        return self._laufen(self._roboter.lied(name))

    def linie_erkannt(self, nummer, farbe='schwarz'):
        """Sieht Bodensensor 1-5 gerade "schwarz" oder "weiss"? True oder False.
        """
        return self._laufen(self._roboter.linie_erkannt(nummer, farbe))

    def links(self, grad=90):
        """Dreht sich auf der Stelle nach links.
        """
        return self._laufen(self._roboter.links(grad))

    def pause(self, schlaege=1):
        """Eine Pause in der Musik.
        """
        return self._laufen(self._roboter.pause(schlaege))

    def rad_drehen(self, rad, wert, einheit='grad', tempo=50, richtung='uhrzeigersinn'):
        """Lässt ein Rad drehen. rad: "links", "rechts" oder "beide";
        einheit: "grad", "umdrehungen" oder "sekunden"; richtung: "uhrzeigersinn" oder "gegen".
        """
        return self._laufen(self._roboter.rad_drehen(rad, wert, einheit, tempo, richtung))

    def rad_stopp(self, rad='beide'):
        """Hält ein Rad an ("links", "rechts" oder "beide").
        """
        return self._laufen(self._roboter.rad_stopp(rad))

    def radabstand(self, millimeter):
        """Stellt den Abstand zwischen den Rädern ein (für genaueres Drehen).
        """
        return self._laufen(self._roboter.radabstand(millimeter))

    def raddurchmesser(self, millimeter):
        """Stellt den Raddurchmesser ein (für genaueres Fahren).
        """
        return self._laufen(self._roboter.raddurchmesser(millimeter))

    def raeder(self, links, rechts):
        """Steuert beide Räder einzeln: -100 (zurück) bis 100 (vor). 0 hält ein Rad an.
        """
        return self._laufen(self._roboter.raeder(links, rechts))

    def rechts(self, grad=90):
        """Dreht sich auf der Stelle nach rechts.
        """
        return self._laufen(self._roboter.rechts(grad))

    def roh(self, befehl, zeitlimit=15):
        """Führt beliebigen MicroPython-Code des Roboters aus (siehe docs/firmware-api/) und gibt
        die Antwort als Text zurück. Beispiel: `await roboter.roh("motion.stop_moving()")`.
        """
        return self._laufen(self._roboter.roh(befehl, zeitlimit))

    def rueckwaerts(self, zentimeter=10):
        """Fährt die angegebene Strecke rückwärts.
        """
        return self._laufen(self._roboter.rueckwaerts(zentimeter))

    def schreibe(self, text):
        """Schreibt einen Text als Laufschrift auf das Display (Umlaute werden evtl. nicht gezeigt).
        """
        return self._laufen(self._roboter.schreibe(text))

    def sende_infrarot(self, text):
        """Schickt eine Nachricht per Infrarot an einen anderen Roboter.
        """
        return self._laufen(self._roboter.sende_infrarot(text))

    def sensorwerte(self):
        """Alle Sensorwerte auf einmal (aktueller Stand) als Wörterbuch.
        """
        return self._laufen(self._roboter.sensorwerte())

    def sieht_farbe(self, farbe):
        """Sieht der Farbsensor unten diese Farbe? Antwort: True oder False.
        Farben: weiss, rot, gelb, gruen, blau, lila, schwarz
        """
        return self._laufen(self._roboter.sieht_farbe(farbe))

    def spiele_datei(self, pfad, warten=True):
        """Spielt eine Ton-Datei ab (mp3, wav oder amr), die auf dem Roboter liegt,
        z. B. "/sdcard/music/effect/24-aircraft.mp3".
        """
        return self._laufen(self._roboter.spiele_datei(pfad, warten))

    def sprich(self, text):
        """Der Roboter spricht – aber nur Englisch (Wörter, Zahlen und Punkte).
        """
        return self._laufen(self._roboter.sprich(text))

    def stoppe(self):
        """Hält den Roboter an.
        """
        return self._laufen(self._roboter.stoppe())

    def strecke_mit_tempo(self, millimeter, tempo=50, warten=True):
        """Fährt eine Strecke in Millimetern mit einstellbarem Tempo (0-100).
        Negative Zahlen fahren rückwärts. Mit warten=False geht das Programm sofort weiter.
        """
        return self._laufen(self._roboter.strecke_mit_tempo(millimeter, tempo, warten))

    def tanze(self, name):
        """Der Roboter tanzt. Mögliche Tänze: tango, walzer, steppen, samba, polonaise, jazz,
        rock, polka
        """
        return self._laufen(self._roboter.tanze(name))

    def tempo(self, geschwindigkeit):
        """Wie schnell gespielt wird (große Zahl = schnell).
        """
        return self._laufen(self._roboter.tempo(geschwindigkeit))

    def ton(self, note='c', schlaege=1, oktave=4):
        """Spielt einen Ton. note: c d e f g a h (h ist das deutsche 'b'); schlaege: Länge;
        oktave: 3 tiefer, 4 normal, 5 höher.
        """
        return self._laufen(self._roboter.ton(note, schlaege, oktave))

    def ton_stopp(self):
        """Beendet die Musik oder das Geräusch.
        """
        return self._laufen(self._roboter.ton_stopp())

    def trommel(self, name, schlaege=1):
        """Spielt eine Trommel (Namen vom Hersteller nicht dokumentiert, z. B. "snare").
        """
        return self._laufen(self._roboter.trommel(name, schlaege))

    def untergrund(self, nummer):
        """Wie hell ist der Boden unter dem Sensor 1 bis 5? 0 = dunkel (Linie), 100 = hell.
        """
        return self._laufen(self._roboter.untergrund(nummer))

    def vorwaerts(self, zentimeter=10):
        """Fährt die angegebene Strecke nach vorne.
        """
        return self._laufen(self._roboter.vorwaerts(zentimeter))

    def warte(self, sekunden):
        """Wartet, ohne etwas zu tun.
        """
        return self._laufen(self._roboter.warte(sekunden))

    def warte_bis(self, bedingung, zeitlimit=30):
        """Wartet, bis `bedingung(sensorwerte)` wahr ist. Gibt True zurück, sonst nach
        dem Zeitlimit False.

            await roboter.warte_bis(lambda werte: werte["abstand_cm"] < 10)
        """
        return self._laufen(self._roboter.warte_bis(bedingung, zeitlimit))

    def zeige_bild(self, zeilen):
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
        return self._laufen(self._roboter.zeige_bild(zeilen))

    def zeige_bild_fuer(self, zeilen, sekunden):
        """Wie `zeige_bild`, aber nur für einige Sekunden.
        """
        return self._laufen(self._roboter.zeige_bild_fuer(zeilen, sekunden))

    def zeige_pixel(self, spalte, zeile, helligkeit=100):
        """Lässt einen einzelnen Punkt leuchten (spalte 0-15, zeile 0-7, helligkeit 0-100).
        """
        return self._laufen(self._roboter.zeige_pixel(spalte, zeile, helligkeit))
