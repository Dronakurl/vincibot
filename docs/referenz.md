# Alle Befehle auf einen Blick

*Diese Datei wird automatisch aus dem Code erzeugt (`python werkzeuge/erzeuge_referenz.py`).*
*In `VinciBotAsync` (async) heißen alle Befehle gleich, man schreibt nur `await` davor.*

## Fahren

### `vorwaerts(zentimeter: 'float' = 10) -> 'None'`

Fährt die angegebene Strecke nach vorne.

### `rueckwaerts(zentimeter: 'float' = 10) -> 'None'`

Fährt die angegebene Strecke rückwärts.

### `links(grad: 'float' = 90) -> 'None'`

Dreht sich auf der Stelle nach links.

### `rechts(grad: 'float' = 90) -> 'None'`

Dreht sich auf der Stelle nach rechts.

### `fahre(richtung: 'str' = 'vorwaerts', tempo: 'int' = 50) -> 'None'`

Fährt immer weiter, bis du `stoppe()` aufrufst.

richtung: "vorwaerts", "rueckwaerts", "links" oder "rechts"
tempo:    0 (langsam) bis 100 (schnell)

### `stoppe() -> 'None'`

Hält den Roboter an.

### `raeder(links: 'int', rechts: 'int') -> 'None'`

Steuert beide Räder einzeln: -100 (zurück) bis 100 (vor). 0 hält ein Rad an.

### `strecke_mit_tempo(millimeter: 'float', tempo: 'int' = 50, warten: 'bool' = True) -> 'None'`

Fährt eine Strecke in Millimetern mit einstellbarem Tempo (0-100).
Negative Zahlen fahren rückwärts. Mit warten=False geht das Programm sofort weiter.

### `drehe_mit_tempo(grad: 'float', tempo: 'int' = 50, warten: 'bool' = True) -> 'None'`

Dreht um einen Winkel mit einstellbarem Tempo. Positiv = links, negativ = rechts
(so macht es auch die Scratch-Oberfläche des Herstellers).

### `rad_drehen(rad: 'str', wert: 'float', einheit: 'str' = 'grad', tempo: 'int' = 50, richtung: 'str' = 'uhrzeigersinn') -> 'None'`

Lässt ein Rad drehen. rad: "links", "rechts" oder "beide";
einheit: "grad", "umdrehungen" oder "sekunden"; richtung: "uhrzeigersinn" oder "gegen".

### `rad_stopp(rad: 'str' = 'beide') -> 'None'`

Hält ein Rad an ("links", "rechts" oder "beide").

### `raddurchmesser(millimeter: 'float') -> 'None'`

Stellt den Raddurchmesser ein (für genaueres Fahren).

### `radabstand(millimeter: 'float') -> 'None'`

Stellt den Abstand zwischen den Rädern ein (für genaueres Drehen).

### `fahr_einstellungen_zuruecksetzen() -> 'None'`

Setzt Raddurchmesser, Radabstand usw. auf die Werkseinstellung zurück.

## Lichter (die 6 bunten LEDs)

### `licht(farbe: 'Farbe') -> 'None'`

Alle sechs Lichter in einer Farbe, z. B. licht("rot") oder licht((255, 0, 128)).

### `licht_einzeln(nummer: 'int', farbe: 'Farbe') -> 'None'`

Ein einzelnes Licht (Nummer 1 bis 6) in einer Farbe.

### `lichter(farben: 'Sequence[Farbe]') -> 'None'`

Alle sechs Lichter einzeln, z. B. lichter(["rot", "gelb", "gruen", "blau", "lila", "weiss"]).

### `licht_aus() -> 'None'`

Schaltet alle Lichter aus.

## Display vorne

### `schreibe(text: 'str') -> 'None'`

Schreibt einen Text als Laufschrift auf das Display (Umlaute werden evtl. nicht gezeigt).

### `zeige_bild(zeilen: 'Sequence[str]') -> 'None'`

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

### `zeige_bild_fuer(zeilen: 'Sequence[str]', sekunden: 'float') -> 'None'`

Wie `zeige_bild`, aber nur für einige Sekunden.

### `zeige_pixel(spalte: 'int', zeile: 'int', helligkeit: 'int' = 100) -> 'None'`

Lässt einen einzelnen Punkt leuchten (spalte 0-15, zeile 0-7, helligkeit 0-100).

### `display_helligkeit(prozent: 'int') -> 'None'`

Stellt die Helligkeit des Displays ein (0 bis 100).

### `display_richtung(richtung: 'str') -> 'None'`

In welche Richtung die Laufschrift wandert: "hoch", "runter", "links", "rechts".

### `display_drehen(richtung: 'str' = 'uhrzeigersinn') -> 'None'`

Dreht das Bild auf dem Display: "uhrzeigersinn" oder "gegen".

### `display_aus() -> 'None'`

Löscht das Display.

## Gefühle, Tänze, Bewegungen

### `gefuehl(name: 'str') -> 'None'`

Der Roboter zeigt ein Gefühl (Gesicht, Ton und Bewegung).

Mögliche Gefühle: froehlich, wuetend, traurig, ueberrascht, aengstlich, angeekelt,
begeistert, schwindelig, muede, schlaefrig, wach, stolz

### `tanze(name: 'str') -> 'None'`

Der Roboter tanzt. Mögliche Tänze: tango, walzer, steppen, samba, polonaise, jazz,
rock, polka

### `bewege_dich(name: 'str') -> 'None'`

Der Roboter macht eine Bewegung. Mögliche Bewegungen: umschauen, verletzt,
sprinten, kreisen, schuetteln

## Töne und Musik

### `geraeusch(name: 'str', warten: 'bool' = True) -> 'None'`

Spielt ein Geräusch ab. Mögliche Geräusche: krankenwagen, polizei, feuerwehr, zug,
zugpfeife, schiffshorn, flugzeug, auto, automotor, magnetbahn

### `lied(name: 'str', warten: 'bool' = True) -> 'None'`

Spielt ein Lied ab. Mögliche Lieder: funkel, jingle bells, geburtstag, freude,
holzsoldaten, jagdpolka

### `sprich(text: 'str', warten: 'bool' = True) -> 'None'`

Der Roboter spricht – aber nur Englisch (Wörter, Zahlen und Punkte).

### `ton(note: 'str' = 'c', schlaege: 'float' = 1, oktave: 'int' = 4) -> 'None'`

Spielt einen Ton. note: c d e f g a h (h ist das deutsche 'b'); schlaege: Länge;
oktave: 3 tiefer, 4 normal, 5 höher.

### `ton_hoehe(midi_nummer: 'int', schlaege: 'float' = 1) -> 'None'`

Spielt einen Ton nach MIDI-Notennummer (60 = mittleres C, 69 = Kammerton a).

### `pause(schlaege: 'float' = 1) -> 'None'`

Eine Pause in der Musik.

### `instrument(name: 'str') -> 'None'`

Wählt das Instrument für `ton()`, z. B. "klavier", "gitarre", "floete", "spieluhr".

### `tempo(geschwindigkeit: 'int') -> 'None'`

Wie schnell gespielt wird (große Zahl = schnell).

### `tempo_aendern(aenderung: 'float') -> 'None'`

Erhöht (positive Zahl) oder senkt (negative Zahl) das Spieltempo.

### `aktuelles_tempo() -> 'float | None'`

Gibt das aktuelle Spieltempo der Musik zurück.

### `trommel(name: 'str', schlaege: 'float' = 1) -> 'None'`

Spielt eine Trommel (Namen vom Hersteller nicht dokumentiert, z. B. "snare").

### `spiele_datei(pfad: 'str', warten: 'bool' = True) -> 'None'`

Spielt eine Ton-Datei ab (mp3, wav oder amr), die auf dem Roboter liegt,
z. B. "/sdcard/music/effect/24-aircraft.mp3".

### `lautstaerke(prozent: 'int | None' = None) -> 'int | None'`

Ohne Zahl: gibt die Lautstärke zurück. Mit Zahl (0 bis 100): stellt sie ein.

### `lautstaerke_aendern(aenderung: 'int') -> 'None'`

Macht den Roboter lauter (positive Zahl) oder leiser (negative Zahl).

### `ton_stopp() -> 'None'`

Beendet die Musik oder das Geräusch.

## Sensoren

### `abstand() -> 'float | None'`

Wie weit ist das nächste Hindernis vorne entfernt? (in Zentimetern)

### `helligkeit(seite: 'str' = 'links') -> 'float | None'`

Wie hell ist es? seite: "links" oder "rechts"; Ergebnis in Prozent.

### `untergrund(nummer: 'int') -> 'int | None'`

Wie hell ist der Boden unter dem Sensor 1 bis 5? 0 = dunkel (Linie), 100 = hell.

### `lautstaerke_umgebung() -> 'int | None'`

Wie laut ist es um den Roboter herum?

### `sieht_farbe(farbe: 'str') -> 'bool | None'`

Sieht der Farbsensor unten diese Farbe? Antwort: True oder False.
Farben: weiss, rot, gelb, gruen, blau, lila, schwarz

### `taste_gedrueckt(taste: 'str') -> 'bool | None'`

Wird eine Taste des Roboters gerade gedrückt? taste: "dreieck", "quadrat" oder "kreis".

### `farbwert(kanal: 'str') -> 'int | None'`

Wie viel Rot, Grün oder Blau sieht der Farbsensor? kanal: "rot", "gruen", "blau".

### `hindernis_naeher_als(zentimeter: 'float') -> 'bool | None'`

Ist ein Hindernis näher als die angegebene Entfernung? True oder False.

### `linie_erkannt(nummer: 'int', farbe: 'str' = 'schwarz') -> 'bool | None'`

Sieht Bodensensor 1-5 gerade "schwarz" oder "weiss"? True oder False.

### `sensorwerte() -> 'Sensorwerte | None'`

Alle Sensorwerte auf einmal (aktueller Stand) als Wörterbuch.

### `farbsensor_kalibrieren() -> 'None'`

Eicht den Farbsensor. Vorher den Roboter auf eine weiße Fläche stellen.

## Infrarot

### `sende_infrarot(text: 'str') -> 'None'`

Schickt eine Nachricht per Infrarot an einen anderen Roboter.

### `empfange_infrarot() -> 'str | None'`

Die zuletzt empfangene Infrarot-Nachricht (oder leer).

### `infrarot_angekommen(text: 'str') -> 'bool | None'`

Wurde genau diese Infrarot-Nachricht empfangen? True oder False.

### `fernbedienung(taste: 'str') -> 'bool | None'`

Wurde diese Taste der Infrarot-Fernbedienung gedrückt? Tasten: volume, mode, speed,
forward, backward, left, right, play, dance, led, music, 1, 2, 3

## Warten

### `warte(sekunden: 'float') -> 'None'`

Wartet, ohne etwas zu tun.

### `warte_bis(bedingung: 'Callable[[Sensorwerte], bool]', zeitlimit: 'float' = 30) -> 'bool'`

Wartet, bis `bedingung(sensorwerte)` wahr ist. Gibt True zurück, sonst nach
dem Zeitlimit False.

    await roboter.warte_bis(lambda werte: werte["abstand_cm"] < 10)

### `sensorstrom(intervall: 'float' = 0.2) -> 'AsyncIterator[Sensorwerte]'`

Liefert fortlaufend die aktuellen Sensorwerte:

async for werte in roboter.sensorstrom():
    print(werte["abstand_cm"])

## Für Fortgeschrittene

### `roh(befehl: 'str', zeitlimit: 'float' = 15) -> 'str | None'`

Führt beliebigen MicroPython-Code des Roboters aus (siehe docs/firmware-api/) und gibt
die Antwort als Text zurück. Beispiel: `await roboter.roh("motion.stop_moving()")`.
