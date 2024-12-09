import array

from locations.react_server_components import parse_rsc


def test_parse_rsc():
    data_raw = b"""4:J"JSON data with tag"
3:["JSON data with no tag"]
2:T14,Raw text with length1:{"x":"No preceding newline"}
0:oa,Byte array"""
    parsed = list(parse_rsc(data_raw))
    assert parsed == [
        (4, "JSON data with tag"),
        (3, ["JSON data with no tag"]),
        (2, "Raw text with length"),
        (1, {"x": "No preceding newline"}),
        (0, array.array("B", b"Byte array")),
    ]
