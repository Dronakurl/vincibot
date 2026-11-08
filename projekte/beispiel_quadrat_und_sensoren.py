"""Testprogramm"""

import random

from vincibot import VinciBot

zaehler = 0

with VinciBot() as roboter:
    roboter.licht("gruen")
    roboter.schreibe("Hallo!")
    for ecke in range(4):
        roboter.vorwaerts(15)
        roboter.rechts(90)
    while True:
        zaehler += 1
        abstand = roboter.abstand()
        if abstand is not None and abstand < 20:
            roboter.licht((255, 0, 0))
            roboter.rueckwaerts(5)
        elif roboter.sieht_farbe("blau") and not roboter.taste_gedrueckt("kreis"):
            roboter.gefuehl("froehlich")
        else:
            roboter.tanze("walzer")
        roboter.warte(random.randint(1, 3))
        roboter.ton("c", 1)
        roboter.zeige_bild(["................"] * 8)
        roboter.fahre("vorwaerts", 40 + zaehler)
        roboter.stoppe()
        eine_funktion_die_es_nicht_gibt = 3
        roboter.sprich("hello")
        roboter.licht_einzeln(3, "rot")
