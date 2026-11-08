from vincibot import _protokoll as p


def test_befehlspaket_stimmt_mit_der_offiziellen_web_app_ueberein():
    # Mitschnitt der Web-App (vinci.matatastudio.com): 10 cm vorwärts
    erwartet = bytes.fromhex(
        "fe 2e 70 00 00 6d 6f 74 69 6f 6e 2e 6d 6f 76 65 5f 70 6f 73 69 74 69 6f 6e 28 22 66 6f "
        "72 77 61 72 64 22 2c 20 31 30 2c 20 22 63 6d 22 29 29 fa")
    assert p.baue_befehlspaket('motion.move_position("forward", 10, "cm")', 0) == erwartet


def test_begruessung_stimmt_mit_der_web_app_ueberein():
    assert p.baue_paket([126, 2, 2, 0, 0]) == bytes.fromhex("fe 07 7e 02 02 00 00 97 77")
    assert p.baue_paket([1, 1]) == bytes.fromhex("fe 04 01 01 33 4c")


def test_entpacken_der_antwort():
    puffer = list(bytes.fromhex("fe 06 7e 01 00 00 0b 96"))
    assert p.entpacke(puffer) == [[0x7E, 0x01, 0x00, 0x00]]
    assert puffer == []


def test_text_mit_umlauten():
    assert p.text_literal("Grüße") == "'Gr\\u00fc\\u00dfe'"
