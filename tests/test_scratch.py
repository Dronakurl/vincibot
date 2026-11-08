# pyright: reportPrivateUsage=false, reportAny=false, reportImplicitStringConcatenation=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
# pyright: reportExplicitAny=false
from typing import Any
import json
import zipfile
from pathlib import Path

import pytest

from vincibot.scratch import (UmwandlungsFehler, python_datei_zu_scratch, python_zu_scratch,
                              scratch_zu_python)

WURZEL = Path(__file__).resolve().parent.parent
BEISPIEL = WURZEL / "projekte" / "Scratch-Projekt.mc"

PROGRAMM = '''
import random
from vincibot import VinciBot

zaehler = 0
with VinciBot() as roboter:
    roboter.licht("gruen")
    for ecke in range(4):
        roboter.vorwaerts(15)
        roboter.rechts(90)
    while True:
        zaehler += 1
        if roboter.abstand() < 20:
            roboter.licht((255, 0, 0))
        elif roboter.sieht_farbe("blau") and not roboter.taste_gedrueckt("kreis"):
            roboter.gefuehl("froehlich")
        else:
            roboter.tanze("walzer")
        roboter.warte(random.randint(1, 3))
        roboter.ton("c", 1)
        roboter.licht_einzeln("links oben", "rot")
'''


@pytest.mark.skipif(not BEISPIEL.exists(), reason="Beispielprojekt fehlt")
def test_beispielprojekt_wird_zu_gueltigem_python():
    ergebnis = scratch_zu_python(BEISPIEL)
    _ = compile(ergebnis.inhalt, "aus_scratch.py", "exec")
    code = ergebnis.inhalt
    assert "def bei_taste_dreieck()" in code
    assert "roboter.schreibe('hello')" in code
    assert "roboter.tanze('polonaise')" in code
    assert "roboter.licht((215, 24, 230))" in code
    assert "roboter.ton_hoehe(60, 0.25)" in code
    assert "for _ in range(10):" in code


@pytest.mark.skipif(not BEISPIEL.exists(), reason="Beispielprojekt fehlt")
def test_display_bild_wird_richtig_gelesen():
    code = scratch_zu_python(BEISPIEL).inhalt
    # Zeile 1 des ersten Bildes im Beispiel: 0001100110011000
    assert "'...##..##..##...'" in code


def _konsistent(projekt: dict[str, Any]) -> list[str]:
    bloecke = projekt["targets"][1]["blocks"]
    fehler: list[str] = []
    for bid, b in bloecke.items():
        for schluessel in ("next", "parent"):
            if b[schluessel] is not None and b[schluessel] not in bloecke:
                fehler.append(f"{bid}.{schluessel}")
        for name, wert in b["inputs"].items():
            for teil in wert[1:]:
                if isinstance(teil, str) and teil not in bloecke:
                    fehler.append(f"{bid}.{name}")
    return fehler


def test_python_zu_scratch_ergibt_konsistentes_projekt():
    ergebnis = python_zu_scratch(PROGRAMM, "test")
    projekt = ergebnis.inhalt["project.json"]
    assert _konsistent(projekt) == []
    opcodes = {b["opcode"] for b in projekt["targets"][1]["blocks"].values()}
    assert {"matatacarEvents_whenRobotStart", "control_repeat", "control_forever", "control_if_else",
            "matatacarMotion_movePosition", "matatacarMotion_moveAngle", "operator_lt",
            "matatacarSensors_getObstacleDistance", "matatacarPerformance_doDance",
            "operator_random", "data_changevariableby"} <= opcodes
    assert any("licht_einzeln" in w for w in ergebnis.warnungen)
    assert "matatacarMotion" in projekt["extensions"]


def test_rundlauf_python_scratch_python(tmp_path: Path):
    py = tmp_path / "prog.py"
    _ = py.write_text(PROGRAMM, encoding="utf-8")
    _ = python_datei_zu_scratch(py)
    zurueck = scratch_zu_python(tmp_path / "prog.mc").inhalt
    _ = compile(zurueck, "zurueck.py", "exec")
    for erwartet in ("roboter.licht((0, 255, 0))", "for _ in range(4):", "roboter.vorwaerts(15)",
                     "roboter.rechts(90)", "while True:", "zaehler += 1", "roboter.abstand() < 20",
                     "roboter.sieht_farbe('blau')", "roboter.tanze('walzer')",
                     "random.randint(1, 3)", "roboter.ton_hoehe(60, 1)"):
        assert erwartet in zurueck, erwartet


def test_projektdatei_ist_ein_zip_mit_project_json(tmp_path: Path):
    py = tmp_path / "klein.py"
    _ = py.write_text("from vincibot import VinciBot\nwith VinciBot() as r:\n    r.vorwaerts(10)\n",
                      encoding="utf-8")
    _ = python_datei_zu_scratch(py)
    with zipfile.ZipFile(tmp_path / "klein.mc") as archiv:
        projekt = json.loads(archiv.read("project.json"))
        assert all(name in archiv.namelist() for t in projekt["targets"] for c in t["costumes"]
                   for name in [c["md5ext"]])


def test_syntaxfehler_und_kein_projekt_geben_klare_fehler(tmp_path: Path):
    with pytest.raises(UmwandlungsFehler):
        _ = python_zu_scratch("for :")
    kaputt = tmp_path / "kaputt.mc"
    _ = kaputt.write_bytes(b"das ist kein projekt")
    with pytest.raises(UmwandlungsFehler):
        _ = scratch_zu_python(kaputt)


def test_nicht_unterstuetztes_wird_gemeldet():
    ergebnis = python_zu_scratch("def f():\n    pass\nimport os\nos.system('x')\n")
    assert any("Funktionen" in w for w in ergebnis.warnungen)
    assert any("os.system" in w for w in ergebnis.warnungen)
