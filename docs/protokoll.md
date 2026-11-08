# Das Bluetooth-Protokoll des VinciBot

Abgeleitet aus der offiziellen Web-Oberfläche (https://vinci.matatastudio.com, Datei `lib.min.js`) und
geprüft gegen deren Bluetooth-Verkehr (Mitschnitt per Browser-Automation).

## Gerät
- Bluetooth-Name `VinciBot_<Nummer>`, Chip ESP32-S3, Firmware: MicroPython
- Per USB meldet er sich als `303a:8136 matatalab device vincibot` (serielle Schnittstelle + USB-Laufwerk
  mit `main.py`, `default.py`, `extention/`, `resources/`). Über USB läuft dasselbe Protokoll.

## Bluetooth
Nordic UART Service `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- Schreiben: `6e400002-…` (in Stücken von 20 Bytes)
- Meldungen (Notify): `6e400003-…` – jede Meldung kommt doppelt an (wird ignoriert)

## Paketformat
```
0xFE | Länge | Nutzdaten ... | CRC16 (Hi, Lo)
```
- Länge = Anzahl Nutzdaten + 2
- `0xFE` → `0xFD 0xDE`, `0xFD` → `0xFD 0xDD` (gilt für Länge, Nutzdaten und CRC)
- CRC16: Startwert `0xFFFF`, zuerst über das Längenbyte, dann über die Nutzdaten
  (siehe `vincibot/_protokoll.py`)

## Begrüßung (nach dem Verbinden)
Ohne sie führt der Roboter keine Befehle aus (nur ein Piepton):

| Nutzdaten | Bedeutung | Antwort |
|---|---|---|
| `7e 02 02 00 00` | neues Protokoll einschalten | `fe 06 7e 01 00 00 0b 96` |
| `01 01` | Version abfragen | `01 01 <major> <minor> <patch> …` (z. B. 1.2.4); in der Bibliothek: `firmware_version()` |

## Befehle
Nutzdaten: `70 00 <Sequenz> <Python-Befehl als ASCII>`, z. B. `motion.move_position("forward", 10, "cm")`.

Der Roboter antwortet mit `70 00 <Sequenz> <Status> <Ergebnistext>`:
- Status `0` = ausgeführt, `255` = Fehler (Text `exec error`)
- Ergebnistext = Rückgabewert als Text (`70`, `True`, `46.0`, `None` …)
- Die Antwort kommt, wenn der Befehl fertig ist (z. B. nach der Fahrt)

Die Sequenznummer ordnet Antworten den Befehlen zu (siehe `SEQUENZ` in `_protokoll.py`). Zahlen stammen
aus der Web-Oberfläche (`commandSequence`).

## Sensorstrom
Der Roboter sendet laufend (mehrmals pro Sekunde) ein Paket mit den Sensorwerten:

| Byte | Bedeutung |
|---|---|
| 0 | `0x74` (Kennung) |
| 1, 2 | Umgebungshelligkeit links, rechts |
| 3–7 | fünf Bodensensoren (0 dunkel … 100 hell) |
| 8 | Geräuschpegel |
| 9–11 | Farbsensor Rot, Grün, Blau |
| 12–13 | Abstand in Zehntel-Zentimetern (High, Low) |
| 14 | Lautstärke |
| 15 | Tempo |

Weitere Paketarten: `0x33` Tasten, `0x7e` Infrarot (laut Web-Oberfläche).

## Tipps
- Der Roboter akzeptiert nur **eine** Verbindung gleichzeitig.
- Befehle mit falschen Argumenten (z. B. Zahl statt Name) lösen Fehlertöne aus. Die offizielle
  Beschreibung der Roboter-Befehle gibt es im Python-Editor auf vinci.matatastudio.com.

## Firmware
- Die Version kommt in den Bytes 2–4 der Antwort auf `01 01` (Stand dieser Doku: Roboter mit **1.2.4**).
- Die Web-Oberfläche verlangt für die Motor-Erweiterung mindestens **V1.2.3** (und V1.2.0 für das
  AI-Vision-Modul) und bietet sonst ein Update an.
- Update-Wege laut Web-Oberfläche: per WLAN (der Roboter lädt die Firmware selbst, `ota.ota_start()`) oder
  über USB mit der Wiederherstellungs-Datei
  `https://matatalab-ota.oss-accelerate.aliyuncs.com/vincibot/vincibot_firmware_for_recovery.bin`
  (Datei vom 08.04.2026, 16,7 MB; Wiederherstellung nur mit Anleitung des Herstellers!).
- Eine öffentliche Liste der VinciBot-Firmware-Versionen habe ich nicht gefunden. Auf
  matatastudio.com/download.html liegt nur die Firmware der *MatataBot* (V3.1.5). Welche Version die
  neueste ist, sagt die Web-Oberfläche beim Verbinden.
