"""Der Roboter tanzt, und die Lichter blinken in bunten Farben."""
from vincibot import VinciBot

with VinciBot() as roboter:
    roboter.lichter(["rot", "gelb", "gruen", "blau", "lila", "weiss"])
    roboter.tanze("samba")
    roboter.licht_aus()
