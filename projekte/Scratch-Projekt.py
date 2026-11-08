"""Automatisch aus dem Scratch-Projekt "Scratch-Projekt" erzeugt (vincibot.scratch)."""

from vincibot import VinciBot

def bei_taste_dreieck() -> None:
    roboter.bewege_dich('umschauen')
    roboter.gefuehl('froehlich')
    roboter.tanze('polonaise')


def bei_taste_dreieck_2() -> None:
    roboter.schreibe('hello')
    roboter.vorwaerts(10)
    roboter.vorwaerts(10)
    roboter.vorwaerts(10)
    roboter.vorwaerts(10)
    roboter.vorwaerts(10)
    roboter.strecke_mit_tempo(10 * 10, 100, False)
    roboter.strecke_mit_tempo(10 * 10, 100, True)
    roboter.bewege_dich('umschauen')
    roboter.bewege_dich('umschauen')
    roboter.tanze('tango')
    roboter.zeige_bild_fuer(['...##..##..##...', '...##..##..##...', '...##..##..##...', '...##..##..##...', '...##..##..##...', '...##..##..##...', '................', '...##..##..##...'], 2)
    roboter.zeige_bild_fuer(['...##..##..##...', '...##..##..##...', '...##..##..##...', '...##..##..##...', '...##..##..##...', '...##..##..##...', '................', '...##..##..##...'], 2)
    roboter.zeige_bild_fuer(['................', '..###......###..', '.....#....#.....', '...##......##...', '..####....####..', '..####....####..', '..####....####..', '................'], 2)
    roboter.zeige_bild_fuer(['................', '..###......###..', '................', '..###......###..', '.###.#....###.#.', '.###.#....###.#.', '.#...#....#...#.', '..###......###..'], 2)
    roboter.zeige_bild_fuer(['................', '..........###...', '.........#####..', '..####...#####..', '....###..###.#..', '..####...#...#..', '..........###...', '................'], 2)
    roboter.licht((215, 24, 230))
    roboter.licht((48, 23, 230))
    roboter.licht((22, 178, 230))
    roboter.zeige_bild(['...........##...', '.........##.##..', '..........##....', '................', '..#...#..#...#..', '...###....###...', '................', '.......##.......'])
    roboter.schreibe('hello')
    roboter.licht((50, 50, 50))
    for _ in range(10):
        roboter.ton_hoehe(60, 0.25)


with VinciBot() as roboter:

    # Ereignisse: Tasten und Sensoren werden laufend abgefragt (Strg+C beendet)
    ereignisse = [
        (lambda: roboter.taste_gedrueckt('dreieck') is True, bei_taste_dreieck),
        (lambda: roboter.taste_gedrueckt('dreieck') is True, bei_taste_dreieck_2),
    ]
    vorher = [False] * len(ereignisse)
    try:
        while True:
            for nr, (bedingung, aktion) in enumerate(ereignisse):
                jetzt = bedingung()
                if jetzt and not vorher[nr]:
                    aktion()
                vorher[nr] = jetzt
            roboter.warte(0.1)
    except KeyboardInterrupt:
        pass
