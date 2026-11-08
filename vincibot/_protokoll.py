"""Internes: Aufbau der Bluetooth-Pakete (für Anfänger nicht nötig)."""
from collections.abc import Iterable
from typing import TypedDict

class Sensorwerte(TypedDict):
    """Die aktuellen Messwerte des Roboters."""
    hell_links: int
    hell_rechts: int
    linie: list[int]
    geraeusch: int
    farbe: tuple[int, int, int]
    abstand_cm: float
    lautstaerke: int
    tempo: int


# Sequenznummern: Der Bot nummeriert Befehlsarten durch und antwortet mit derselben Nummer.
SEQUENZ: dict[str, int] = {
    "strecke": 0, "winkel": 1, "fahrt_start": 2, "fahrt_stopp": 3,
    "strecke_tempo": 4, "winkel_tempo": 5, "motor_lauf": 6, "motor_tempo": 8, "motor_stopp": 9,
    "tanz": 10, "emotion": 11, "verhalten": 12, "bild": 16, "text": 17, "anzeige_aus": 18,
    "helligkeit": 19, "pixel": 20, "ausrichtung": 21, "led_feld": 22, "anzeige_drehen": 23,
    "led_alle": 26, "led_einzeln": 27, "led_aus": 28,
    "effekt": 31, "lied": 33, "sprich": 35, "datei": 37, "ton_stopp": 38,
    "lautstaerke": 39, "trommel": 43, "pause": 44, "note": 45, "instrument": 46, "tempo": 47,
    "ir_senden": 52, "abfrage": 0,
}

# Begrüßung nach dem Verbinden (wie in der offiziellen Web-Oberfläche)
BEGRUESSUNG: list[list[int]] = [[126, 2, 2, 0, 0], [1, 1]]


def pruefsumme(daten: Iterable[int], startwert: int = 0xFFFF) -> int:
    ergebnis = startwert
    for byte in daten:
        ergebnis = ((ergebnis >> 8) | (ergebnis << 8)) & 0xFFFF
        ergebnis ^= byte
        ergebnis ^= (ergebnis & 0xFF) >> 4
        ergebnis ^= (ergebnis << 12) & 0xFFFF
        ergebnis ^= ((ergebnis & 0xFF) << 5) & 0xFFFF
    return ergebnis


def _maskiere(byte: int) -> list[int]:
    if byte == 0xFE:
        return [0xFD, 0xDE]
    if byte == 0xFD:
        return [0xFD, 0xDD]
    return [byte]


def baue_paket(nutzdaten: list[int]) -> bytes:
    """Startbyte 0xFE, Länge, Nutzdaten, Prüfsumme (Sonderbytes werden maskiert)."""
    laenge = len(nutzdaten) + 2
    summe = pruefsumme(nutzdaten, pruefsumme([laenge]))
    paket: list[int] = [0xFE] + _maskiere(laenge)
    for byte in nutzdaten:
        paket += _maskiere(byte)
    paket += _maskiere(summe >> 8) + _maskiere(summe & 0xFF)
    return bytes(paket)


def baue_befehlspaket(code: str, sequenz: int) -> bytes:
    """Paket für einen Python-Befehl, den der Bot ausführt."""
    return baue_paket([0x70, 0x00, sequenz] + list(code.encode("ascii", "replace")))


def text_literal(text: object) -> str:
    """Macht aus beliebigem Text ein Python-Textstück für den Bot (Umlaute als \\uXXXX)."""
    teile: list[str] = []
    for zeichen in str(text):
        if zeichen in "\\'\"":
            teile.append("\\" + zeichen)
        elif ord(zeichen) > 127:
            teile.append("\\u%04x" % ord(zeichen))
        else:
            teile.append(zeichen)
    return "'" + "".join(teile) + "'"


def entpacke(puffer: list[int]) -> list[list[int]]:
    """Holt vollständige Pakete aus einem Byte-Puffer. Gibt (liste_von_nutzdaten) zurück
    und entfernt Verarbeitetes aus dem Puffer."""
    pakete: list[list[int]] = []
    while True:
        if 0xFE not in puffer:
            puffer.clear()
            return pakete
        del puffer[:puffer.index(0xFE)]
        roh: list[int] = []
        i = 1
        ende = None
        while i < len(puffer):
            b = puffer[i]
            if b == 0xFD and i + 1 < len(puffer):
                roh.append(0xFE if puffer[i + 1] == 0xDE else 0xFD)
                i += 2
            elif b == 0xFD:
                break
            else:
                roh.append(b)
                i += 1
            if roh and len(roh) >= roh[0] + 1:
                ende = i
                break
        if ende is None:
            return pakete          # Paket noch unvollständig
        del puffer[:ende]
        pakete.append(roh[1:roh[0] - 1])
