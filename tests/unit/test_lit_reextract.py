r"""K8 extractor regressions found by the AI pre-check (DEC-033/036): header grid, significance letters,
thousands separators. Each case is a real cell format from the stored papers."""
import xml.etree.ElementTree as ET

import pytest

from tools.reextract_literature_v1 import NUM, ND, RANGE, convention, grid, to_number


@pytest.mark.parametrize("cell,value,sd", [
    ("12.3 ± 0.4", "12.3", "0.4"), ("12.3 ± 0.4 (ab)", "12.3", "0.4"), ("28.04 ± 1.84 C,A", "28.04", "1.84"),
    ("0.754 b", "0.754", ""), ("99.94%", "99.94", ""), ("31.31% remaining", "31.31", ""),
    ("10,454.85 ± 88.73 a", "10454.85", "88.73"), ("19,100 ± 11,300", "19100", "11300"),
])
def test_values_parse(cell, value, sd):
    m = NUM.match(cell)
    assert m, cell
    assert to_number(m.group("v"), "dot")[0] == value
    assert to_number(m.group("sd") or "", "dot")[0] == sd


def test_separator_rules_never_guess():
    assert to_number("19,100", "dot") == ("19100", "THOUSANDS_SEP")
    assert to_number("19,100", "comma") == ("19.100", "DECIMAL_COMMA")
    assert to_number("19,100", "unknown") == ("", "AMBIGUOUS_SEPARATOR")
    assert to_number("12,5", "unknown") == ("12.5", "DECIMAL_COMMA")
    assert convention(["1.2", "19,100"]) == "dot" and convention(["12,5", "3,25"]) == "comma"


def test_non_detects_and_ranges():
    assert ND.match("nd") and ND.match("n.d.") and ND.match("<LOD") and ND.match("nd 3")
    assert RANGE.match("23.7-42.5") and not NUM.match("1080/1071") and not NUM.match("2,5-Dimethylpyrazine")


def test_header_grid_respects_colspan_and_rowspan():
    t = ET.fromstring("<table><thead><tr><th rowspan='2'>Sample</th><th colspan='2'>Oil</th></tr>"
                      "<tr><th>Soybean</th><th>Olive</th></tr></thead></table>")
    g = grid(t.findall("./thead/tr"))
    assert [x[0] for x in g[0]] == ["Sample", "Oil", "Oil"]
    assert [x[0] for x in g[1]] == ["Sample", "Soybean", "Olive"]
