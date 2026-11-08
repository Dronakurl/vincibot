"""Für Fortgeschrittene: Mit `async` macht der Roboter mehrere Dinge gleichzeitig.
Hier fährt er 20 cm und leuchtet dabei bunt."""
import asyncio
from vincibot import VinciBotAsync


async def haupt():
    async with VinciBotAsync() as roboter:
        _ = await asyncio.gather(
            roboter.vorwaerts(20),
            roboter.lichter(["rot", "gelb", "gruen", "blau", "lila", "weiss"]),
        )
        await roboter.licht_aus()


asyncio.run(haupt())
