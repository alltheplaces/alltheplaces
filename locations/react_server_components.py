import array
import itertools
import json
from typing import Any, Iterable, Iterator

# Maps from Flight tags to Python array/struct type codes
ARRAY_TYPES = {"O": "b", "o": "B", "S": "h", "s": "H", "L": "l", "l": "L", "G": "f", "g": "d", "M": "q", "m": "Q"}


def parse_rsc(data_raw: Iterable[int]) -> Iterator[tuple[int, Any]]:
    """Parse a React "Flight" stream, used for React Server Components.
    There is no formal or human-readable specification for this format. The React source code for parsing it is here:
    https://github.com/facebook/react/blob/e1378902bbb322aa1fe1953780f4b2b5f80d26b1/packages/react-client/src/ReactFlightClient.js
    This code references that code (start with processBinaryChunk), but simplified to use iterators instead of a state
    machine, and only returns JSON objects instead of fully deserializing.
    """
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
