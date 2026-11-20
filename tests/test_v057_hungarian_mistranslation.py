"""v0.5.7: regression from a real Environment Agency news brief."""
from pathlib import Path

from hungarian_language import polish_hungarian, check_hungarian_language
from editorial_quality import numeric_values


USER_EXAMPLE = (
    "Eddie Moorcroft hat hónap börtönbüntetést kapott, amely egy évre "
    "felfüggesztett, valamint 10,000 font pénzbírságot a jogellenes hulladéklerakásért. "
    "Philip Fairbrother 6,000 font bírságot kapott, mivel ő szervezte meg a hulladék "
    "szállítását. A felderítés során 36 őrizetbe vétel történt a "
    "hulladékrémállyal kapcsolatosan április óta. "
    "A jogellenes hulladéklerakásból Moorcroft több mint 71,000 fontot keresett. "
    "A bírósági határozat alapján a vádlottaknak 16,000 fontot kell fizetniük "
    "a Környezetvédelmi Ügynökség költségeinek fedezésére."
)


def test_actual_bad_english_to_hungarian_news_example():
    revised = polish_hungarian(USER_EXAMPLE)
    assert "hulladékrémál" not in revised
    assert "illegális hulladékkezeléssel kapcsolatosan" in revised
    for value in ("10 000 font", "6 000 font", "71 000 fontot", "16 000 fontot"):
        assert value in revised
    assert "36 őrizetbe vétel" in revised
    assert check_hungarian_language(revised)[0]
    assert numeric_values(USER_EXAMPLE) == numeric_values(revised)


def test_bare_decimal_and_plain_statistics_unmodified():
    originals = [
        "A 0,125 százalékpontos emelkedés nem 125-ös érték.",
        "A 6,000 mg-os érték egy precíz mérési adat.",
        "A 4,125 milliós ráta statisztika.",
        "A bruttó 70,1%-os emelkedés 2025.11.20. napján történt.",
    ]
    for original in originals:
        assert polish_hungarian(original) == original


def test_ambiguous_text_detected_without_making_up_definitions():
    assert check_hungarian_language("36 ember a hulladékrémállyal kapcsolatban.")[0] is False
    assert check_hungarian_language("36 őrizetbe vétel hulladékkal kapcsolatos bűnügyekben.")[0]


def test_prompt_refers_to_source_checked_waste_crime_and_factuality():
    code = (Path(__file__).resolve().parents[1] / "orbisacta.py").read_text(encoding="utf-8")
    assert 'English "waste crime"' in code
    assert '36 arrests in relation to waste crime since April' in code
    assert 'against the unchanged direct source evidence' in code
