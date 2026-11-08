"""Der Roboter fährt ein Quadrat. Mit einer Schleife wiederholst du Befehle."""
from vincibot import VinciBot

with VinciBot() as roboter:
    for seite in range(4):          # viermal wiederholen
        roboter.vorwaerts(15)       # 15 Zentimeter geradeaus
        roboter.rechts(90)          # Ecke: 90 Grad nach rechts
