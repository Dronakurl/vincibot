"""Spiele eine kleine Melodie: "Alle meine Entchen" (c d e f g g)."""
from vincibot import VinciBot

with VinciBot() as roboter:
    roboter.instrument("klavier")
    for note in ["c", "d", "e", "f"]:
        roboter.ton(note, 1)
    roboter.ton("g", 2)
    roboter.ton("g", 2)
