"""vincibot – den VinciBot (MatataStudio) per Bluetooth mit Python steuern."""
from .roboter import VinciBot
from .asynchron import VinciBotAsync
from ._protokoll import Sensorwerte
from ._woerter import RoboterFehler, FARBEN
from ._verbindung import VerbindungsFehler

__all__ = ["VinciBot", "VinciBotAsync", "RoboterFehler", "VerbindungsFehler", "Sensorwerte", "FARBEN"]
__version__ = "0.2.0"
