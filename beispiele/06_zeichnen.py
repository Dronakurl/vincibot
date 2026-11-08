"""Male ein Bild auf das Display: '#' leuchtet, '.' bleibt dunkel (8 Zeilen, 16 Zeichen)."""
from vincibot import VinciBot

herz = [
    "................",
    "...###....###...",
    "..#####..#####..",
    "..############..",
    "...##########...",
    "....########....",
    ".....######.....",
    "......####......",
]

with VinciBot() as roboter:
    roboter.zeige_bild(herz)
    roboter.warte(5)
    roboter.display_aus()
