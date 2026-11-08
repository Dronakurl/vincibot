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
8. [Wenn etwas nicht klappt](#8-wenn-etwas-nicht-klappt)
9. [Wie funktioniert das?](#9-wie-funktioniert-das)
10. [Für Entwickler](#10-für-entwickler)

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
2. Der Roboter darf **nicht gleichzeitig** mit einem anderen Programm verbunden sein, zum Beispiel mit der MatataCode-Seite im Browser (dort vorher auf "Trennen" klicken oder den Tab schließen). Er kann nur mit einem Gerät sprechen.
3. Dein Programm sucht den Roboter selbst. Beim Verbinden piept er einmal – das ist normal.

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
| ein einzelnes Licht (1–6) | `licht_einzeln(3, "gelb")` |
| sechs Lichter bunt | `lichter(["rot", "gelb", "gruen", "blau", "lila", "weiss"])` |
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
            roboter.lichter(["rot", "gelb", "gruen", "blau", "lila", "weiss"]),
        )

asyncio.run(haupt())
```

Außerdem gibt es `await roboter.warte_bis(lambda werte: werte["abstand_cm"] < 10)` und `async for werte in roboter.sensorstrom(): ...` für fortlaufende Sensorwerte.

## 8. Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| „Kein VinciBot gefunden“ | Roboter einschalten, näher an den Computer, Bluetooth am Computer aktivieren. Prüfen, dass er nicht mit einem anderen Gerät (Tablet, Browser) verbunden ist. Unter Linux hilft `bluetoothctl disconnect <Adresse>`. |
| Der Roboter piept mehrmals | Ein Befehl war unpassend (z. B. ein Wert außerhalb des erlaubten Bereichs). Ein Piepen beim Verbinden ist normal. |
| Der Roboter reagiert gar nicht mehr | Aus- und wieder einschalten, danach neu verbinden. |
| `ModuleNotFoundError: vincibot` | Die Python-Umgebung ist nicht eingeschaltet (`source .venv/bin/activate`). |
| Umlaute auf dem Display fehlen | Das Display zeigt nicht alle Sonderzeichen. Schreibe „ae“, „oe“, „ue“. |
| `sprich(...)` versteht deutsche Wörter nicht | Der Roboter spricht nur Englisch. |

## 9. Wie funktioniert das?

Der VinciBot ist ein kleiner Computer (ESP32-S3), auf dem MicroPython läuft. Dieses Paket sendet per Bluetooth Low Energy kleine Pakete mit MicroPython-Befehlen wie `motion.move_position("forward", 10, "cm")`. Der Roboter führt sie aus, antwortet und meldet laufend seine Sensorwerte. Das Paketformat wurde aus der offiziellen Web-Oberfläche (vinci.matatastudio.com) abgeleitet und gegen deren Bluetooth-Verkehr geprüft. Details: [docs/protokoll.md](docs/protokoll.md). Die offizielle Beschreibung der Roboter-Befehle liegt in [docs/firmware-api/](docs/firmware-api/).

## 10. Für Entwickler

```
vincibot/
  roboter.py       einfache Klasse VinciBot (ohne async), AUTOMATISCH erzeugt aus asynchron.py
  asynchron.py     VinciBotAsync – alle Befehle, async
  _woerter.py      deutsche Namen (Farben, Tänze …) -> Befehle des Roboters
  _verbindung.py   Bluetooth-Verbindung, Antworten, Sensorstrom
  _protokoll.py    Paketformat, Prüfsumme
beispiele/         Beispielprogramme
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

Getestet am echten Roboter (Linux, BlueZ): Fahren, Drehen, Lichter, Display (Text, Bild, Pixel), Töne, Noten, Lied „funkel“, Sprechen, Gefühle, Bewegungen, Tänze, Sensorabfragen und gleichzeitige Befehle. Die Namen aller Geräusche, Tänze, Gefühle und Bewegungen wurden einmal durchgespielt und vom Roboter angenommen. Nicht ausprobiert: die übrigen Lieder (außer „funkel“), `spiele_datei`, Infrarot, Fernbedienung, Farbsensor-Kalibrierung und die Trommel-Namen.
