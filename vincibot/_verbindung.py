"""Internes: Bluetooth-Verbindung (asynchron). Anfänger nutzen stattdessen `VinciBot`."""
import asyncio
import time
from dataclasses import dataclass

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

from ._protokoll import BEGRUESSUNG, Sensorwerte, baue_befehlspaket, baue_paket, entpacke

SCHREIB_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
MELDUNG_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
PAKETGROESSE = 20


class VerbindungsFehler(Exception):
    """Der Roboter konnte nicht gefunden oder verbunden werden."""


@dataclass(frozen=True)
class Antwort:
    """Die Antwort des Roboters auf einen Befehl."""
    sequenz: int
    status: int
    text: str

    @property
    def fehler(self) -> bool:
        return self.status != 0

class Verbindung:
    def __init__(self, adresse: str | None = None, namensanfang: str = "VinciBot",
                 suchdauer: float = 15) -> None:
        self.adresse: str | None = adresse
        self.namensanfang: str = namensanfang
        self.suchdauer: float = suchdauer
        self.sensoren: Sensorwerte | None = None
        self._client: BleakClient | None = None
        self._puffer: list[int] = []
        self._erwartet: dict[int, asyncio.Future[Antwort]] = {}
        self._begruessung: asyncio.Future[list[int]] | None = None
        self._letzte_meldung: tuple[bytes, float] = (b"", 0.0)

    async def verbinden(self) -> None:
        if self.adresse:
            geraet = await BleakScanner.find_device_by_address(self.adresse, timeout=self.suchdauer)
        else:
            geraet = await BleakScanner.find_device_by_filter(
                lambda g, _: bool(g.name) and g.name.startswith(self.namensanfang),
                timeout=self.suchdauer)
        if geraet is None:
            raise VerbindungsFehler(
                "Kein VinciBot gefunden. Ist er eingeschaltet und nicht schon mit einem anderen"
                + " Programm oder Browser verbunden?")
        self._client = BleakClient(geraet)
        await self._client.connect()
        await self._client.start_notify(MELDUNG_UUID, self._bei_meldung)
        for nutzdaten in BEGRUESSUNG:
            self._begruessung = asyncio.get_running_loop().create_future()
            await self._sende(baue_paket(nutzdaten))
            try:
                _ = await asyncio.wait_for(self._begruessung, 3)
            except asyncio.TimeoutError:
                pass

    async def trennen(self) -> None:
        if self._client is not None:
            try:
                await self._client.disconnect()
            finally:
                self._client = None

    async def _sende(self, paket: bytes) -> None:
        assert self._client is not None, "Nicht verbunden"
        for anfang in range(0, len(paket), PAKETGROESSE):
            await self._client.write_gatt_char(
                SCHREIB_UUID, paket[anfang:anfang + PAKETGROESSE], response=True)

    def _bei_meldung(self, _: BleakGATTCharacteristic, daten: bytearray) -> None:
        # Der Roboter schickt jede Meldung doppelt; die zweite Kopie wird ignoriert.
        jetzt = time.monotonic()
        if bytes(daten) == self._letzte_meldung[0] and jetzt - self._letzte_meldung[1] < 0.2:
            return
        self._letzte_meldung = (bytes(daten), jetzt)
        self._puffer.extend(daten)
        for nutzdaten in entpacke(self._puffer):
            self._verarbeite(nutzdaten)

    def _verarbeite(self, n: list[int]) -> None:
        if not n:
            return
        if n[0] == 0x74 and len(n) >= 16:
            self.sensoren = Sensorwerte(
                hell_links=n[1], hell_rechts=n[2], linie=[n[3], n[4], n[5], n[6], n[7]],
                geraeusch=n[8], farbe=(n[9], n[10], n[11]),
                abstand_cm=((n[12] << 8) | n[13]) / 10, lautstaerke=n[14], tempo=n[15])
        elif n[0] == 0x70 and len(n) >= 4:
            antwort = Antwort(n[2], n[3], bytes(n[4:]).decode("utf-8", "replace"))
            erwartet = self._erwartet.pop(antwort.sequenz, None)
            if erwartet and not erwartet.done():
                erwartet.set_result(antwort)
        elif self._begruessung and not self._begruessung.done():
            self._begruessung.set_result(n)

    async def befehl(self, code: str, sequenz: int = 0, zeitlimit: float = 15) -> Antwort | None:
        """Führt einen Python-Befehl auf dem Bot aus und wartet auf seine Antwort."""
        zukunft: asyncio.Future[Antwort] = asyncio.get_running_loop().create_future()
        self._erwartet[sequenz] = zukunft
        await self._sende(baue_befehlspaket(code, sequenz))
        try:
            return await asyncio.wait_for(zukunft, zeitlimit)
        except asyncio.TimeoutError:
            _ = self._erwartet.pop(sequenz, None)
            return None
