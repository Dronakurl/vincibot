"""Eine Ampel mit den sechs Lichtern."""
from vincibot import VinciBot

with VinciBot() as roboter:
    for runde in range(3):
        roboter.licht("rot");   roboter.warte(2)
        roboter.licht("gelb");  roboter.warte(1)
        roboter.licht("gruen"); roboter.warte(2)
    roboter.licht_aus()
