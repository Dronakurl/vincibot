"""Für Fortgeschrittene: Mit `async` macht der Roboter mehrere Dinge gleichzeitig.
Hier fährt er 20 cm und leuchtet dabei bunt."""
import asyncio
from vincibot import VinciBotAsync


async def haupt():
    async with VinciBotAsync() as roboter:
        _ = await asyncio.gather(
            roboter.vorwaerts(20),
            roboter.lichter({
                "links oben": "rot", "links mitte": "gelb", "links unten": "gruen",
                "rechts unten": "blau", "rechts mitte": "lila", "rechts oben": "weiss",
            }),
        )
        await roboter.licht_aus()


asyncio.run(haupt())
