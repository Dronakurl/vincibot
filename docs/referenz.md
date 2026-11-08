# Alle Befehle auf einen Blick

*Diese Datei wird automatisch aus dem Code erzeugt (`python werkzeuge/erzeuge_referenz.py`).*
*In `VinciBotAsync` (async) heißen alle Befehle gleich, man schreibt nur `await` davor.*

## Fahren

### `vorwaerts(zentimeter=10)`

Fährt die angegebene Strecke nach vorne.

### `rueckwaerts(zentimeter=10)`

Fährt die angegebene Strecke rückwärts.

### `links(grad=90)`

Dreht sich auf der Stelle nach links.

### `rechts(grad=90)`

Dreht sich auf der Stelle nach rechts.

### `fahre(richtung='vorwaerts', tempo=50)`

Fährt immer weiter, bis du `stoppe()` aufrufst.

richtung: "vorwaerts", "rueckwaerts", "links" oder "rechts"
tempo:    0 (langsam) bis 100 (schnell)

### `stoppe()`

Hält den Roboter an.

### `raeder(links, rechts)`

Steuert beide Räder einzeln: -100 (zurück) bis 100 (vor). 0 hält ein Rad an.

### `strecke_mit_tempo(millimeter, tempo=50, warten=True)`

Fährt eine Strecke in Millimetern mit einstellbarem Tempo (0-100).
Negative Zahlen fahren rückwärts. Mit warten=False geht das Programm sofort weiter.

### `drehe_mit_tempo(grad, tempo=50, warten=True)`

Dreht um einen Winkel mit einstellbarem Tempo. Positiv = rechts, negativ = links.

### `rad_drehen(rad, wert, einheit='grad', tempo=50, richtung='uhrzeigersinn')`

Lässt ein Rad drehen. rad: "links", "rechts" oder "beide";
einheit: "grad", "umdrehungen" oder "sekunden"; richtung: "uhrzeigersinn" oder "gegen".

### `rad_stopp(rad='beide')`

Hält ein Rad an ("links", "rechts" oder "beide").

### `raddurchmesser(millimeter)`

Stellt den Raddurchmesser ein (für genaueres Fahren).

### `radabstand(millimeter)`

Stellt den Abstand zwischen den Rädern ein (für genaueres Drehen).

### `fahr_einstellungen_zuruecksetzen()`

Setzt Raddurchmesser, Radabstand usw. auf die Werkseinstellung zurück.

## Lichter (die 6 bunten LEDs)

### `licht(farbe)`

Alle sechs Lichter in einer Farbe, z. B. licht("rot") oder licht((255, 0, 128)).

### `licht_einzeln(nummer, farbe)`

Ein einzelnes Licht (Nummer 1 bis 6) in einer Farbe.

### `lichter(farben)`

Alle sechs Lichter einzeln, z. B. lichter(["rot", "gelb", "gruen", "blau", "lila", "weiss"]).

### `licht_aus()`

Schaltet alle Lichter aus.

## Display vorne

### `schreibe(text)`

Schreibt einen Text als Laufschrift auf das Display (Umlaute werden evtl. nicht gezeigt).

### `zeige_bild(zeilen)`

Zeigt ein Bild, das du mit Zeichen malst: 8 Zeilen mit je 16 Zeichen.
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

### `zeige_bild_fuer(zeilen, sekunden)`

Wie `zeige_bild`, aber nur für einige Sekunden.

### `zeige_pixel(spalte, zeile, helligkeit=100)`

Lässt einen einzelnen Punkt leuchten (spalte 0-15, zeile 0-7, helligkeit 0-100).

### `display_helligkeit(prozent)`

Stellt die Helligkeit des Displays ein (0 bis 100).

### `display_richtung(richtung)`

In welche Richtung die Laufschrift wandert: "hoch", "runter", "links", "rechts".

### `display_drehen(richtung='uhrzeigersinn')`

Dreht das Bild auf dem Display: "uhrzeigersinn" oder "gegen".

### `display_aus()`

Löscht das Display.

## Gefühle, Tänze, Bewegungen

### `gefuehl(name)`

Der Roboter zeigt ein Gefühl (Gesicht, Ton und Bewegung).

Mögliche Gefühle: froehlich, wuetend, traurig, ueberrascht, aengstlich, angeekelt,
begeistert, schwindelig, muede, schlaefrig, wach, stolz

### `tanze(name)`

Der Roboter tanzt. Mögliche Tänze: tango, walzer, steppen, samba, polonaise, jazz,
rock, polka

### `bewege_dich(name)`

Der Roboter macht eine Bewegung. Mögliche Bewegungen: umschauen, verletzt,
sprinten, kreisen, schuetteln

## Töne und Musik

### `geraeusch(name)`

Spielt ein Geräusch ab. Mögliche Geräusche: krankenwagen, polizei, feuerwehr, zug,
zugpfeife, schiffshorn, flugzeug, auto, automotor, magnetbahn

### `lied(name)`

Spielt ein Lied ab. Mögliche Lieder: funkel, jingle bells, geburtstag, freude,
holzsoldaten, jagdpolka

### `sprich(text)`

Der Roboter spricht – aber nur Englisch (Wörter, Zahlen und Punkte).

### `ton(note='c', schlaege=1, oktave=4)`

Spielt einen Ton. note: c d e f g a h (h ist das deutsche 'b'); schlaege: Länge;
oktave: 3 tiefer, 4 normal, 5 höher.

### `pause(schlaege=1)`

Eine Pause in der Musik.

### `instrument(name)`

Wählt das Instrument für `ton()`, z. B. "klavier", "gitarre", "floete", "spieluhr".

### `tempo(geschwindigkeit)`

Wie schnell gespielt wird (große Zahl = schnell).

### `aktuelles_tempo()`

Gibt das aktuelle Spieltempo der Musik zurück.

### `trommel(name, schlaege=1)`

Spielt eine Trommel (Namen vom Hersteller nicht dokumentiert, z. B. "snare").

### `spiele_datei(pfad, warten=True)`

Spielt eine Ton-Datei ab (mp3, wav oder amr), die auf dem Roboter liegt,
z. B. "/sdcard/music/effect/24-aircraft.mp3".

### `lautstaerke(prozent=None)`

Ohne Zahl: gibt die Lautstärke zurück. Mit Zahl (0 bis 100): stellt sie ein.

### `lautstaerke_aendern(aenderung)`

Macht den Roboter lauter (positive Zahl) oder leiser (negative Zahl).

### `ton_stopp()`

Beendet die Musik oder das Geräusch.

## Sensoren

### `abstand()`

Wie weit ist das nächste Hindernis vorne entfernt? (in Zentimetern)

### `helligkeit(seite='links')`

Wie hell ist es? seite: "links" oder "rechts"; Ergebnis in Prozent.

### `untergrund(nummer)`

Wie hell ist der Boden unter dem Sensor 1 bis 5? 0 = dunkel (Linie), 100 = hell.

### `lautstaerke_umgebung()`

Wie laut ist es um den Roboter herum?

### `sieht_farbe(farbe)`

Sieht der Farbsensor unten diese Farbe? Antwort: True oder False.
Farben: weiss, rot, gelb, gruen, blau, lila, schwarz

### `farbwert(kanal)`

Wie viel Rot, Grün oder Blau sieht der Farbsensor? kanal: "rot", "gruen", "blau".

### `hindernis_naeher_als(zentimeter)`

Ist ein Hindernis näher als die angegebene Entfernung? True oder False.

### `linie_erkannt(nummer, farbe='schwarz')`

Sieht Bodensensor 1-5 gerade "schwarz" oder "weiss"? True oder False.

### `sensorwerte()`

Alle Sensorwerte auf einmal (aktueller Stand) als Wörterbuch.

### `farbsensor_kalibrieren()`

Eicht den Farbsensor. Vorher den Roboter auf eine weiße Fläche stellen.

## Infrarot

### `sende_infrarot(text)`

Schickt eine Nachricht per Infrarot an einen anderen Roboter.

### `empfange_infrarot()`

Die zuletzt empfangene Infrarot-Nachricht (oder leer).

### `infrarot_angekommen(text)`

Wurde genau diese Infrarot-Nachricht empfangen? True oder False.

### `fernbedienung(taste)`

Wurde diese Taste der Infrarot-Fernbedienung gedrückt? Tasten: volume, mode, speed,
forward, backward, left, right, play, dance, led, music, 1, 2, 3

## Warten

### `warte(sekunden)`

Wartet, ohne etwas zu tun.

### `warte_bis(bedingung, zeitlimit=30)`

Wartet, bis `bedingung(sensorwerte)` wahr ist. Gibt True zurück, sonst nach
dem Zeitlimit False.

    await roboter.warte_bis(lambda werte: werte["abstand_cm"] < 10)

### `sensorstrom(intervall=0.2)`

Liefert fortlaufend die aktuellen Sensorwerte:

async for werte in roboter.sensorstrom():
    print(werte["abstand_cm"])

## Für Fortgeschrittene

### `roh(befehl, zeitlimit=15)`

Führt beliebigen MicroPython-Code des Roboters aus (siehe docs/firmware-api/) und gibt
die Antwort als Text zurück. Beispiel: `await roboter.roh("motion.stop_moving()")`.
