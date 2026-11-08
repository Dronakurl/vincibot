# vincibot – den VinciBot mit Python steuern

Mit diesem Paket steuerst du den Lernroboter **VinciBot** von MatataStudio mit Python – per Bluetooth, auf Deutsch und ganz ohne Vorkenntnisse. Die Befehle lesen sich wie normale Sätze:

```python
from vincibot import VinciBot

with VinciBot() as roboter:
    roboter.licht("gruen")        # alle Lichter grün
    roboter.vorwaerts(10)         # 10 Zentimeter nach vorne
    roboter.rechts(90)            # nach rechts drehen
    roboter.schreibe("Hallo!")    # Laufschrift auf dem Display
    roboter.tanze("samba")        # tanzen
```

> Dieses Projekt ist **inoffiziell** und steht in keiner Verbindung zu MatataStudio / Matatalab.
> Es wurde mit einem VinciBot unter Linux entwickelt und getestet.

## Inhalt

1. [Was du brauchst](#1-was-du-brauchst)
2. [Installieren](#2-installieren)
3. [Roboter verbinden](#3-roboter-verbinden)
4. [Dein erstes Programm](#4-dein-erstes-programm)
5. [Alle Befehle im Überblick](#5-alle-befehle-im-überblick)
6. [Beispielprogramme](#6-beispielprogramme)
7. [Mehrere Dinge gleichzeitig (async)](#7-mehrere-dinge-gleichzeitig-async)
8. [Scratch und Python umwandeln](#8-scratch-und-python-umwandeln)
9. [Wenn etwas nicht klappt](#9-wenn-etwas-nicht-klappt)
10. [Wie funktioniert das?](#10-wie-funktioniert-das)
11. [Für Entwickler](#11-für-entwickler)

## 1. Was du brauchst

- einen **VinciBot** (eingeschaltet, Akku geladen)
- einen Computer mit **Bluetooth** (Linux getestet; Windows und macOS sollten mit der Bluetooth-Bibliothek `bleak` funktionieren, sind aber nicht getestet)
- **Python 3.10 oder neuer**

## 2. Installieren

Öffne ein Terminal im Ordner dieses Projekts und gib ein:

```bash
python3 -m venv .venv                # eigene Python-Umgebung anlegen (einmalig)
source .venv/bin/activate            # Umgebung einschalten (Windows: .venv\Scripts\activate)
pip install -e .                     # vincibot installieren
```

Danach kannst du Programme starten, zum Beispiel: `python beispiele/01_hallo.py`

## 3. Roboter verbinden

1. **Roboter einschalten.**
2. Am Programmende trennt `vincibot` die Verbindung von selbst, auch wenn du `trennen()` vergessen hast. Bleibt der Roboter nach einem abgebrochenen Programm unter Linux als „verbunden“ hängen, löst `vincibot` das beim nächsten Verbinden selbst.
3. Der Roboter darf **nicht gleichzeitig** mit einem anderen Programm verbunden sein, zum Beispiel mit der MatataCode-Seite im Browser (dort vorher auf "Trennen" klicken oder den Tab schließen). Er kann nur mit einem Gerät sprechen.
4. Dein Programm sucht den Roboter selbst. Beim Verbinden piept er einmal – das ist normal.

Gibt es mehrere Roboter in der Nähe, nutzt du die Adresse deines Roboters: `VinciBot(adresse="AA:BB:CC:DD:EE:FF")`. Auf Linux findest du sie mit `bluetoothctl devices`.

## 4. Dein erstes Programm

Speichere dies als `hallo.py` und starte es mit `python hallo.py`:

```python
from vincibot import VinciBot

with VinciBot() as roboter:
    roboter.licht("blau")
    roboter.vorwaerts(10)
    roboter.licht_aus()
```

Was passiert hier?

- `from vincibot import VinciBot` holt den Roboter in dein Programm.
- `with VinciBot() as roboter:` verbindet sich mit dem Roboter und nennt ihn `roboter`. Am Ende wird die Verbindung automatisch beendet.
- Jede Zeile darunter (**eingerückt**!) ist ein Befehl an den Roboter. Er führt sie nacheinander aus.

Mit **Schleifen** wiederholst du Befehle, mit **if** triffst du Entscheidungen:

```python
with VinciBot() as roboter:
    for ecke in range(4):                # 4-mal wiederholen
        roboter.vorwaerts(15)
        roboter.rechts(90)

    if roboter.abstand() < 20:           # ist etwas näher als 20 cm?
        roboter.licht("rot")
```

## 5. Alle Befehle im Überblick

Die wichtigsten Befehle (`roboter.` davor schreiben). Die **vollständige Liste mit Erklärungen** steht in [docs/referenz.md](docs/referenz.md).

| Das willst du … | Befehl |
|---|---|
| vorwärts / rückwärts fahren | `vorwaerts(10)` · `rueckwaerts(10)` (Zentimeter) |
| drehen | `links(90)` · `rechts(45)` (Grad) |
| dauerhaft fahren und anhalten | `fahre("vorwaerts", tempo=50)` · `stoppe()` |
| Lichter einschalten | `licht("rot")` · `licht((255, 0, 128))` |
| ein einzelnes Licht | `licht_einzeln("links oben", "gelb")` – Positionen siehe unten |
| mehrere Lichter bunt | `lichter({"links oben": "rot", "rechts unten": "blau"})` |
| Lichter ausschalten | `licht_aus()` |
| etwas auf das Display schreiben | `schreibe("Hallo")` |
| ein Bild zeigen | `zeige_bild([...])` – siehe Beispiel 06 |
| einen Punkt leuchten lassen | `zeige_pixel(spalte, zeile)` · `display_aus()` |
| ein Gefühl zeigen | `gefuehl("froehlich")` |
| tanzen | `tanze("tango")` |
| eine Bewegung machen | `bewege_dich("umschauen")` |
| ein Geräusch abspielen | `geraeusch("polizei")` |
| ein Lied abspielen | `lied("funkel")` |
| Englisch sprechen | `sprich("hello")` |
| Töne spielen | `ton("c", 1)` · `instrument("gitarre")` |
| lauter / leiser | `lautstaerke(80)` |
| Entfernung messen | `abstand()` (Zentimeter) |
| Helligkeit messen | `helligkeit("links")` |
| Farbe am Boden erkennen | `sieht_farbe("rot")` |
| alle Sensorwerte | `sensorwerte()` |
| warten | `warte(2)` (Sekunden) |

**Die sechs Lichter** heißen nach ihrer Position (von vorne gesehen):

```
links oben    rechts oben
links mitte   rechts mitte
links unten   rechts unten
```

**Werte, die du verwenden kannst**

- **Farben:** rot, gruen, blau, gelb, orange, lila, tuerkis, rosa, weiss, schwarz – oder drei Zahlen von 0 bis 255 für Rot, Grün und Blau, z. B. `(255, 128, 0)`.
- **Gefühle:** froehlich, wuetend, traurig, ueberrascht, aengstlich, angeekelt, begeistert, schwindelig, muede, schlaefrig, wach, stolz
- **Tänze:** tango, walzer, steppen, samba, polonaise, jazz, rock, polka
- **Bewegungen:** umschauen, verletzt, sprinten, kreisen, schuetteln
- **Geräusche:** krankenwagen, polizei, feuerwehr, zug, zugpfeife, schiffshorn, flugzeug, auto, automotor, magnetbahn
- **Lieder:** funkel, jingle bells, geburtstag, freude, holzsoldaten, jagdpolka
- **Noten:** c, d, e, f, g, a, h (mit `oktave=3`, `4` oder `5` tiefer oder höher)

Gibst du etwas Unbekanntes an, sagt dir das Programm in einer deutschen Fehlermeldung, welche Werte möglich sind.

## 6. Beispielprogramme

Im Ordner [`beispiele/`](beispiele/) liegen kleine Programme zum Ausprobieren und Verändern:

| Datei | Was passiert |
|---|---|
| `01_hallo.py` | Der Roboter begrüßt dich mit Licht, Text und Gesicht |
| `02_quadrat.py` | Er fährt ein Quadrat (Schleife) |
| `03_ampel.py` | Eine Ampel aus den sechs Lichtern |
| `04_abstandswarner.py` | Wie ein Einparkpiepser: je näher, desto roter |
| `05_hindernis_ausweichen.py` | Er fährt los und weicht Hindernissen aus |
| `06_zeichnen.py` | Ein Herz auf dem Display |
| `07_musik.py` | Eine kleine Melodie |
| `08_tanzparty.py` | Tanzen und blinken |
| `09_gleichzeitig_async.py` | Fahren und leuchten zur gleichen Zeit |

Tipp: Ändere Zahlen und Farben und schau, was passiert. So lernst du am schnellsten!

## 7. Mehrere Dinge gleichzeitig (async)

Normalerweise wartet das Programm bei jedem Befehl, bis der Roboter fertig ist. Willst du, dass er **gleichzeitig** fährt und leuchtet, nimmst du die Klasse `VinciBotAsync`. Sie kann alles, was `VinciBot` kann; du schreibst nur `async`/`await` dazu:

```python
import asyncio
from vincibot import VinciBotAsync

async def haupt():
    async with VinciBotAsync() as roboter:
        await asyncio.gather(
            roboter.vorwaerts(20),
            roboter.lichter({"links oben": "rot", "rechts oben": "gruen"}),
        )

asyncio.run(haupt())
```

Außerdem gibt es `await roboter.warte_bis(lambda werte: werte["abstand_cm"] < 10)` und `async for werte in roboter.sensorstrom(): ...` für fortlaufende Sensorwerte.

## 8. Scratch und Python umwandeln

Du kennst die Blockprogrammierung von MatataCode (Scratch)? Dann kannst du Projekte in Python-Programme
umwandeln und so sehen, wie die Blöcke als Text aussehen – oder umgekehrt:

```bash
python -m vincibot.scratch projekt.mc       # Scratch  -> projekt.py
python -m vincibot.scratch programm.py      # Python   -> programm.mc  (in MatataCode über Datei → Load from your computer öffnen)
```

Aus „when robot start → move forward 10 cm → turn right 90“ wird:

```python
with VinciBot() as roboter:
    roboter.vorwaerts(10)
    roboter.rechts(90)
```

Was sich nicht umwandeln lässt, meldet der Konverter als **Warnung** – nichts verschwindet stillschweigend.
Zurück nach Scratch klappt nur bei einfachen Programmen (Befehle, Schleifen, if/else, Variablen, Rechnen).
Die Tabelle der Blöcke und alle Grenzen stehen in [docs/scratch.md](docs/scratch.md); Beispiele liegen in
[`projekte/`](projekte/).

## 9. Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| „Kein VinciBot gefunden“ | Roboter einschalten, näher an den Computer, Bluetooth am Computer aktivieren. Prüfen, dass er nicht mit einem anderen Gerät (Tablet, Browser) verbunden ist. Unter Linux hilft `bluetoothctl disconnect <Adresse>`. |
| Der Roboter piept mehrmals | Ein Befehl war unpassend (z. B. ein Wert außerhalb des erlaubten Bereichs). Ein Piepen beim Verbinden ist normal. |
| Der Roboter reagiert gar nicht mehr | Aus- und wieder einschalten, danach neu verbinden. |
| `ModuleNotFoundError: vincibot` | Die Python-Umgebung ist nicht eingeschaltet (`source .venv/bin/activate`). |
| Umlaute auf dem Display fehlen | Das Display zeigt nicht alle Sonderzeichen. Schreibe „ae“, „oe“, „ue“. |
| `sprich(...)` versteht deutsche Wörter nicht | Der Roboter spricht nur Englisch. |

## 10. Wie funktioniert das?

Der VinciBot ist ein kleiner Computer (ESP32-S3), auf dem MicroPython läuft. Dieses Paket sendet per Bluetooth Low Energy kleine Pakete mit MicroPython-Befehlen wie `motion.move_position("forward", 10, "cm")`. Der Roboter führt sie aus, antwortet und meldet laufend seine Sensorwerte. Das Paketformat wurde aus der offiziellen Web-Oberfläche (vinci.matatastudio.com) abgeleitet und gegen deren Bluetooth-Verkehr geprüft. Details: [docs/protokoll.md](docs/protokoll.md). Die offizielle Beschreibung der Roboter-Befehle liegt in [docs/firmware-api/](docs/firmware-api/).

## 11. Für Entwickler

```
vincibot/
  roboter.py       einfache Klasse VinciBot (ohne async), AUTOMATISCH erzeugt aus asynchron.py
  asynchron.py     VinciBotAsync – alle Befehle, async
  _woerter.py      deutsche Namen (Farben, Tänze …) -> Befehle des Roboters
  _verbindung.py   Bluetooth-Verbindung, Antworten, Sensorstrom
  _protokoll.py    Paketformat, Prüfsumme
  scratch.py       Konverter Scratch (.mc/.sb3) <-> Python
beispiele/         Beispielprogramme
projekte/          Scratch-Beispielprojekte und ihre Python-Umwandlung
docs/              Referenz, Protokoll, Roboter-API
tests/             Tests (laufen ohne Roboter): pytest
werkzeuge/         erzeuge_roboter.py (erzeugt roboter.py) und erzeuge_referenz.py (docs/referenz.md)
```

```bash
pip install -e ".[test]"
pytest                                  # Tests ohne Roboter
python werkzeuge/erzeuge_roboter.py      # roboter.py neu erzeugen, nachdem asynchron.py geändert wurde
python werkzeuge/erzeuge_referenz.py    # Referenz neu erzeugen
```

Für Befehle, die dieses Paket nicht kennt, gibt es `roboter.roh("<MicroPython-Befehl>")`. Nicht unterstützt sind bisher die Erweiterungen mit Kamera-Modul (`vision`, `lcd`), WLAN/MQTT und Zusatzmotoren – die API-Beschreibung dafür liegt in `docs/firmware-api/`, und über `roh()` sind sie prinzipiell erreichbar.

### Teststand

Getestet am echten Roboter (Linux, BlueZ): Fahren, Drehen, Lichter, Display (Text, Bild, Pixel), Töne, Noten, Lied „funkel“, Sprechen, Gefühle, Bewegungen, Tänze, Sensorabfragen und gleichzeitige Befehle. Die Namen aller Geräusche, Tänze, Gefühle und Bewegungen wurden einmal durchgespielt und vom Roboter angenommen. Der Scratch-Konverter ist mit einem Beispielprojekt und per Rundlauf getestet; ein erzeugtes Scratch-Projekt wurde in der Web-Oberfläche geladen. Am Roboter bestätigt: Anordnung der Lichter, Bildanzeige, Farben und die Drehrichtung von `drehe_mit_tempo` (positiv = links). Infrarot: Senden und Abfragen laufen ohne Fehler, ein Empfang wurde aber nicht beobachtet. Nicht ausprobiert: ob der Roboter ein umgewandeltes Programm genauso ausführt wie die Blöcke, die übrigen Lieder (außer „funkel“), `spiele_datei`, Empfang von Infrarot und Fernbedienung, Farbsensor-Kalibrierung und die Trommel-Namen.
