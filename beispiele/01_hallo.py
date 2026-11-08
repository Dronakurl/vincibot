"""Dein erstes Programm: Der Roboter begrüßt dich."""
from vincibot import VinciBot

with VinciBot() as roboter:
    roboter.licht("gruen")          # alle Lichter grün
    roboter.schreibe("Hallo!")      # Laufschrift auf dem Display
    roboter.gefuehl("froehlich")    # fröhliches Gesicht
    roboter.licht_aus()
