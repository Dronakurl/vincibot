# Scratch ↔ Python

Der Konverter wandelt Projekte der MatataCode-Oberfläche (`.mc`, ein Scratch-3-Projekt als ZIP) und
Scratch-Dateien (`.sb3`) in Python-Programme für `vincibot` um – und einfache Python-Programme zurück in Blöcke.

```bash
python -m vincibot.scratch projekt.mc      # -> projekt.py   (Scratch -> Python)
python -m vincibot.scratch programm.py     # -> programm.mc  (Python -> Scratch)
vincibot-konverter projekt.mc              # gleiche Wirkung nach `pip install -e .`
```

In Python: `scratch_zu_python(datei)`, `scratch_datei_zu_python(ein, aus)`, `python_zu_scratch(text)`,
`python_datei_zu_scratch(ein, aus)`. Jede Funktion gibt ein `Ergebnis` mit `inhalt` und `warnungen` zurück.

**Was nicht umgewandelt werden kann, wird nie stillschweigend weggelassen:** Es erscheint eine Warnung
(auf der Kommandozeile und in `Ergebnis.warnungen`); im Python-Text steht dann ein Kommentar
`# Nicht unterstützt: <Block>`.

## Verifiziert
- Dein Beispielprojekt `projekte/Scratch-Projekt.mc` wird zu lauffähigem Python (`projekte/Scratch-Projekt.py`).
- Ein aus Python erzeugtes `.mc` (`projekte/beispiel_quadrat_und_sensoren.mc`) wurde in der echten
  Web-Oberfläche (vinci.matatastudio.com → *Load from your computer*) geladen und alle Blöcke wurden
  richtig dargestellt (Variablen, Schleifen, if/else, Sensoren, Gefühle, Tänze, Musik).
- Rundlauf Python → Scratch → Python ergibt wieder dasselbe Programm (Test `test_rundlauf_python_scratch_python`).

**Nicht verifiziert:** dass der Roboter jedes erzeugte Programm genauso ausführt wie die Original-Blöcke
(vor allem die Drehrichtung bei `drehe_mit_tempo`: positiv = links, so wie in der Hersteller-Oberfläche, am Roboter aber nicht nachgeprüft) und die Namen einiger Menüs, die nur im
Python→Scratch-Weg vorkommen (`motionTurn`, `motionAngleUint`, `motionDirection`, `restForBeats`).
Sie wurden aus dem Frontend-Code abgeleitet, nicht an einem Beispielprojekt geprüft.

## Scratch → Python

| Scratch-Block | Python |
|---|---|
| when robot start / green flag | Hauptprogramm (`with VinciBot() as roboter:`) |
| when *Taste* key pressed (Dreieck/Quadrat/Kreis) | Funktion `bei_taste_<taste>()`, aufgerufen von einer Ereignisschleife |
| when obstacle distance / when *Farbe* detected | Funktion + Ereignisschleife |
| wait, repeat, forever, if/else, repeat until, wait until | `warte`, `for`, `while True`, `if/else`, `while not`, `while not … warte` |
| set / change variable | `x = …`, `x += …` (Variablen werden oben angelegt) |
| + − × ÷ mod, round, random, join, length, abs, floor, sqrt | Rechnen, `round`, `random.randint`, … |
| < > =, and, or, not | Vergleiche, `and`, `or`, `not` |
| move *forward/backward* for … cm/inch | `vorwaerts` / `rueckwaerts` |
| turn *left/right* for … degrees/rotations | `links` / `rechts` |
| start moving, stop moving | `fahre`, `stoppe` |
| move/turn … with speed (until done) | `strecke_mit_tempo`, `drehe_mit_tempo` |
| motor run / stop (Motor-Erweiterung) | `rad_drehen`, `rad_stopp` |
| dance / emotion / action | `tanze`, `gefuehl`, `bewege_dich` |
| write, show image (for … s), turn off, brightness, pixel, rotate, orientation | `schreibe`, `zeige_bild(_fuer)`, `display_aus`, `display_helligkeit`, `zeige_pixel`, `display_drehen`, `display_richtung` |
| set all LEDs (Farbe / R,G,B), set LED, all off | `licht`, `licht_einzeln`, `licht_aus` |
| sound / sing / say / audio play (until done) | `geraeusch`, `lied`, `sprich`, `spiele_datei` |
| play note, rest, tempo, instrument | `ton_hoehe`, `pause`, `tempo`, `tempo_aendern`, `instrument` |
| send ir message, ir received | `sende_infrarot`, `infrarot_angekommen` |
| Sensoren: obstacle distance, ambient light, loudness, color value, key pressed, color detected | `abstand`, `helligkeit`, `lautstaerke_umgebung`, `farbwert`, `taste_gedrueckt`, `sieht_farbe` |

Nicht in der deutschen API vorhanden (z. B. ein Effekt oder Lied mit einem Namen, den nur Scratch kennt):
Der Block wird als `roboter.roh("audio.effect(…)")` ausgegeben, sodass er trotzdem funktioniert.

**Nicht unterstützt:** Meine Blöcke, Listen, Nachrichten (`broadcast`), Zeitgeber, Figuren-Blöcke
(Aussehen, Bewegung der Bühnenfigur), mehrere Figuren gleichzeitig, Erweiterungen mit Zusatzhardware
(Kamera, Display, WLAN).

**Unterschied beim Ablauf:** Scratch führt mehrere Skripte *gleichzeitig* aus. Im Python-Text laufen die
Ereignis-Funktionen nacheinander; Tasten werden mit einer Abfrage-Schleife ausgewertet (das Programm
beendest du mit Strg+C).

## Python → Scratch

Unterstützt sind einfache Programme mit `roboter = VinciBot()` oder `with VinciBot() as roboter:`:

- Befehle: `vorwaerts`, `rueckwaerts`, `links`, `rechts`, `fahre`, `stoppe`, `licht` (Name oder Zahlen),
  `licht_aus`, `schreibe`, `zeige_bild`, `zeige_bild_fuer`, `zeige_pixel`, `display_aus`, `display_helligkeit`,
  `gefuehl`, `tanze`, `bewege_dich`, `sprich`, `ton`, `ton_hoehe`, `pause`, `warte`, `time.sleep`
- Schleifen und Entscheidungen: `for … in range(n)`, `while True`, `while <Bedingung>`, `if/elif/else`
- Variablen und Rechnen: `x = …`, `x += …`, `+ - * / %`, `random.randint`, `round`
- Bedingungen: `<`, `>`, `==`, `!=`, `<=`, `>=`, `and`, `or`, `not`, `abstand()`, `hindernis_naeher_als()`,
  `sieht_farbe()`, `taste_gedrueckt()`, `lautstaerke_umgebung()`, `farbwert()`

Alles andere (Funktionen, Klassen, `licht_einzeln`, `lichter`, `geraeusch`, `lied`, Listen, `break` …)
wird übersprungen und als **Warnung mit Zeilennummer** gemeldet. Namen und Zahlen für Menüs (Farben,
Tänze, Gefühle …) müssen **fest im Programm stehen**, nicht in Variablen.

Das Ergebnis ist **ein** Skript unter „when robot start“ in einer Figur („Figur1“) und ein leeres Bühnenbild.

## Wie es funktioniert
Ein `.mc` ist ein ZIP mit `project.json` (Scratch-3-Format) und den Bild-/Tondateien. Die Blöcke der
MatataCode-Erweiterungen heißen `matatacarMotion_movePosition`, `matatacarLight_displayWriteText` usw.;
Auswahlfelder sind eigene Schatten-Blöcke (`…_menu_motionTrend`) mit den englischen Werten der Roboter-API
(`forward`, `cm`, `happy` …). Das Format wurde aus dem Beispielprojekt und dem Frontend-Code abgeleitet.
