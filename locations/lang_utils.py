_KATAKANA = (
    "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトド"
    "ナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶー"
)
_HIRAGANA = (
    "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとど"
    "なにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖー"
)
_KATAKANA_TO_HIRAGANA = str.maketrans(_KATAKANA, _HIRAGANA)


def katakana_to_hiragana(text: str) -> str:
    """
    Convert a katakana string to hiragana for OSM's "ja-Hira" tag.
    """
    return text.translate(_KATAKANA_TO_HIRAGANA)
