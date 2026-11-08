"""Erzeugt vincibot/roboter.py (die einfache Klasse ohne async) aus vincibot/asynchron.py.
Aufruf: python werkzeuge/erzeuge_roboter.py"""
import inspect
import pathlib

from vincibot.asynchron import VinciBotAsync

KOPF = '''"""Die einfache Schnittstelle zum VinciBot – gemacht zum Programmieren lernen (ohne async).

ACHTUNG: Diese Datei wird automatisch erzeugt (python werkzeuge/erzeuge_roboter.py).
Änderungen bitte in asynchron.py machen und die Datei neu erzeugen.
"""
from __future__ import annotations

import asyncio
import atexit
import contextlib
import threading
from collections.abc import Callable, Coroutine, Mapping, Sequence
from types import TracebackType
from typing import TypeVar

from ._protokoll import Sensorwerte
from ._typen import (Bewegung, Bodensensor, DisplayRichtung, Drehrichtung, Einheit, Farbe, Farbkanal,
                     Fernbedienungstaste, FahrRichtung, Gefuehl, Geraeusch, Instrument, Lied, Linienfarbe,
                     Note, Position, Rad, Seite, SensorFarbe, Tanz, Taste)
from .asynchron import VinciBotAsync

_T = TypeVar("_T")


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

    def __init__(self, adresse: str | None = None, suchdauer: float = 15) -> None:
        """Verbindet sich mit dem Roboter.

        adresse:   Nur nötig, wenn mehrere Roboter in der Nähe sind (z. B. "AA:BB:CC:DD:EE:FF").
        suchdauer: Wie viele Sekunden nach dem Roboter gesucht wird.
        """
        self._schleife: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self._faden: threading.Thread = threading.Thread(target=self._schleife.run_forever,
                                                         daemon=True)
        self._faden.start()
        self._roboter: VinciBotAsync = VinciBotAsync(adresse=adresse, suchdauer=suchdauer)
        try:
            self._laufen(self._roboter.verbinden())
        except BaseException:
            self._beende_schleife()
            raise
        self._offen: bool = True
        # Falls `trennen()` vergessen wird, trennt Python beim Programmende automatisch.
        _ = atexit.register(self._beim_beenden)

    def _beim_beenden(self) -> None:
        if self._offen:
            with contextlib.suppress(Exception):
                self.trennen()

    def _laufen(self, aufgabe: Coroutine[object, object, _T]) -> _T:
        return asyncio.run_coroutine_threadsafe(aufgabe, self._schleife).result()

    def _beende_schleife(self) -> None:
        _ = self._schleife.call_soon_threadsafe(self._schleife.stop)
        self._faden.join(timeout=2)

    def trennen(self) -> None:
        """Beendet die Verbindung zum Roboter (geschieht am Programmende auch von selbst)."""
        if not self._offen:
            return
        self._offen = False
        atexit.unregister(self._beim_beenden)
        try:
            self._laufen(self._roboter.trennen())
        finally:
            self._beende_schleife()

    def __enter__(self) -> "VinciBot":
        return self

    def __exit__(self, typ: type[BaseException] | None, wert: BaseException | None,
                 spur: TracebackType | None) -> None:
        self.trennen()
'''


def methode(name, funktion):
    parameter = list(inspect.signature(funktion).parameters.values())[1:]
    signatur = ["self"]
    aufruf = []
    for par in parameter:
        teil = f"{par.name}: {par.annotation}"
        if par.default is not inspect.Parameter.empty:
            teil += f" = {par.default!r}"
        signatur.append(teil)
        aufruf.append(par.name)
    rueckgabe = inspect.signature(funktion).return_annotation
    doc = inspect.cleandoc(funktion.__doc__ or "")
    doc = "\n".join(("        " + z) if z else "" for z in doc.splitlines())
    return (f"    def {name}({', '.join(signatur)}) -> {rueckgabe}:\n"
            f'        """{doc.strip()}\n        """\n'
            f"        return self._laufen(self._roboter.{name}({', '.join(aufruf)}))\n")


def erzeuge():
    teile = [KOPF]
    for name, funktion in inspect.getmembers(VinciBotAsync, inspect.iscoroutinefunction):
        if name.startswith("_") or name in ("verbinden", "trennen"):
            continue
        teile.append("\n" + methode(name, funktion))
    return "".join(teile)


if __name__ == "__main__":
    ziel = pathlib.Path(__file__).resolve().parent.parent / "vincibot" / "roboter.py"
    ziel.write_text(erzeuge(), encoding="utf-8")
    print("vincibot/roboter.py geschrieben")
