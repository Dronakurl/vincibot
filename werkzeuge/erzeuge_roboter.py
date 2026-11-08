"""Erzeugt vincibot/roboter.py (die einfache Klasse ohne async) aus vincibot/asynchron.py.
Aufruf: python werkzeuge/erzeuge_roboter.py"""
import inspect
import pathlib

from vincibot.asynchron import VinciBotAsync

KOPF = '''"""Die einfache Schnittstelle zum VinciBot – gemacht zum Programmieren lernen (ohne async).

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
'''


def methode(name, funktion):
    parameter = list(inspect.signature(funktion).parameters.values())[1:]
    signatur = ["self"]
    aufruf = []
    for par in parameter:
        if par.default is inspect.Parameter.empty:
            signatur.append(par.name)
        else:
            signatur.append(f"{par.name}={par.default!r}")
        aufruf.append(par.name)
    doc = inspect.cleandoc(funktion.__doc__ or "")
    doc = "\n".join(("        " + z) if z else "" for z in doc.splitlines())
    return (f"    def {name}({', '.join(signatur)}):\n"
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
