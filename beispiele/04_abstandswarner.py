"""Wie ein Einparkpiepser: je näher ein Hindernis, desto roter wird das Licht.
Beenden mit Strg+C."""
from vincibot import VinciBot

with VinciBot() as roboter:
    try:
        while True:
            entfernung = roboter.abstand()          # in Zentimetern
            if entfernung is None:
                continue
            if entfernung < 10:
                roboter.licht("rot")
            elif entfernung < 30:
                roboter.licht("gelb")
            else:
                roboter.licht("gruen")
            roboter.warte(0.2)
    except KeyboardInterrupt:
        roboter.licht_aus()
