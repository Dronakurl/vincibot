# pyright: reportPrivateUsage=false
"""Die Literal-Typen müssen genau zu den Wörterbüchern passen, sonst meldet der Linter Falsches."""
from typing import get_args

from vincibot import _typen as t
from vincibot import _woerter as w


def test_literale_passen_zu_den_woerterbuechern():
    paare = [
        (t.Farbname, w.FARBEN), (t.Gefuehl, w.GEFUEHLE), (t.Tanz, w.TAENZE),
        (t.Bewegung, w.BEWEGUNGEN), (t.Geraeusch, w.GERAEUSCHE), (t.Lied, w.LIEDER),
        (t.Note, w.NOTEN), (t.SensorFarbe, w.FARBEN_SENSOR),
    ]
    for literal, woerterbuch in paare:
        assert set(get_args(literal)) == set(woerterbuch), literal
    assert set(get_args(t.Instrument)) == set(w.INSTRUMENTE)
    assert set(get_args(t.Position)) == {k for k in w.POSITIONEN if " " in k}
