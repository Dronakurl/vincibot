"""Der Roboter fährt vorwärts und dreht um, wenn ein Hindernis näher als 15 cm ist.
Beenden mit Strg+C."""
from vincibot import VinciBot

with VinciBot() as roboter:
    try:
        roboter.fahre("vorwaerts", tempo=40)
        while True:
            if roboter.warte_bis(lambda werte: werte["abstand_cm"] < 15, zeitlimit=1):
                roboter.stoppe()
                roboter.rueckwaerts(5)
                roboter.links(120)
                roboter.fahre("vorwaerts", tempo=40)
    except KeyboardInterrupt:
        roboter.stoppe()
