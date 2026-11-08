"""Spiele eine kleine Melodie: "Alle meine Entchen" (c d e f g g)."""
from vincibot import VinciBot

roboter = VinciBot()
roboter.instrument("klavier")
roboter.ton("c", 1)
roboter.ton("d", 1)
roboter.ton("e", 1)
roboter.ton("f", 1)
roboter.ton("g", 2)
roboter.ton("g", 2)
roboter.trennen()
