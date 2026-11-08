"""Die einfache Schnittstelle zum VinciBot – gemacht zum Programmieren lernen (ohne async).

Alle Methoden stammen aus `VinciBotAsync` (siehe asynchron.py) und werden hier automatisch so
verpackt, dass man sie ganz normal aufrufen kann, ohne `async` und `await`.
"""
import asyncio
import functools
import inspect
import threading

from .asynchron import VinciBotAsync


def _verpacke(name, funktion):
    @functools.wraps(funktion)
    def einfach(self, *argumente, **schluesselwoerter):
        return self._laufen(funktion(self._roboter, *argumente, **schluesselwoerter))
    einfach.__name__ = name
    return einfach


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


# Alle normalen (async) Methoden von VinciBotAsync als einfache Methoden übernehmen.
for _name, _funktion in inspect.getmembers(VinciBotAsync, inspect.iscoroutinefunction):
    if not _name.startswith("_") and _name not in ("verbinden", "trennen"):
        setattr(VinciBot, _name, _verpacke(_name, _funktion))


def _warte_bis(self, bedingung, zeitlimit=30):
    """Wartet, bis `bedingung(sensorwerte)` wahr ist (True) – oder bis das Zeitlimit abläuft (False).

        roboter.warte_bis(lambda werte: werte["abstand_cm"] < 10)
    """
    return self._laufen(self._roboter.warte_bis(bedingung, zeitlimit))


VinciBot.warte_bis = _warte_bis
