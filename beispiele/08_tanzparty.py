"""Der Roboter tanzt, und die Lichter blinken in bunten Farben."""
from vincibot import VinciBot

with VinciBot() as roboter:
    roboter.lichter({
        "links oben": "rot", "links mitte": "gelb", "links unten": "gruen",
        "rechts unten": "blau", "rechts mitte": "lila", "rechts oben": "weiss",
    })
    roboter.tanze("samba")
    roboter.licht_aus()
