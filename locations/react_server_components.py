import array
import itertools
import json
from typing import Any, Iterable, Iterator

ARRAY_TYPES = {"O": "b", "o": "B", "S": "h", "s": "H", "L": "l", "l": "L", "G": "f", "g": "d", "M": "q", "m": "Q"}


def parse_rsc(data_raw: Iterable[int]) -> Iterator[tuple[int, Any]]:
    # based on https://github.com/alvarlagerlof/rsc-parser/blob/32f225ab8e0451b7e73144a269e9dd07e83f6fd1/packages/react-client/src/ReactFlightClient.ts#L1595
    data = iter(data_raw)
    while True:
        row_id_str = bytes(itertools.takewhile(lambda c: c != ord(":"), data))
        if len(row_id_str) == 0:
            break
        row_id = int(row_id_str, 16)

        row_tag = chr(next(data))

        if row_tag in "AGLMOSTUVglmos":
            row_length = int(bytes(itertools.takewhile(lambda c: c != ord(","), data)), 16)
            row_data = bytes(itertools.islice(data, row_length))
        else:
            row_data = bytes(itertools.takewhile(lambda c: c != ord("\n"), data))
            if row_tag not in "BCDEFHIJKNPQRWXYZrx":
                row_data = row_tag.encode() + row_data
                row_tag = b"\0"

        if array_type := ARRAY_TYPES.get(row_tag):
            yield row_id, array.array(array_type, row_data)
        else:
            row_str = row_data.decode()

            if row_tag == "H":
                yield row_id, (row_str[0], json.loads(row_str[1:]))
            elif row_tag == "T":
                yield row_id, row_str
            else:
                yield row_id, json.loads(row_str)
