import requests


class NSI(object):
    """
    Interact with Name Suggestion Index (NSI). The NSI distribution is a GIT sub-module of this
    project. As part of their GIT repo the NSI people publish a JSON version of their database
    which is used by the OSM editor to do rather useful brand suggestions when editing POIs.
    It is possible that we move to dynamic API (HTTP) access to the NSI in the future.
    """

    def __init__(self):
        self.nsi_wikidata = None

    def _ensure_loaded(self):
        if self.nsi_wikidata is None:
            self.nsi_wikidata = requests.get(
                "https://raw.githubusercontent.com/osmlab/name-suggestion-index/main/dist/wikidata.min.json"
            ).json()["wikidata"]
            if not self.nsi_wikidata:
                self.nsi_wikidata = {}

    def lookup_wikidata_code(self, brand_wikidata):
        """
        Lookup wikidata code in the NSI.
        :param brand_wikidata: wikidata code to lookup in the NSI
        :return: NSI wikidata.json entry if present
        """
        self._ensure_loaded()
        return self.nsi_wikidata.get(brand_wikidata)

    def lookup_label(self, s):
        """
        Lookup by fuzzy label match in the NSI.
        :param s: string to fuzzy match
        :return: iterator of matching NSI wikidata.json entries
        """
        self._ensure_loaded()
        s = NSI.normalise(s)
        for k, v in self.nsi_wikidata.items():
            if label := v.get("label"):
                if s in NSI.normalise(label):
                    yield k, v

    @staticmethod
    def normalise(s):
        """
        Help fuzzy matcher by "normalising" string data.
        :param s: string to be cleaned
        :return: the cleaned string
        """
        s = s.upper()
        converted_word = ""
        for char in s:
            if char in NSI.replace_table:
                replace_char = NSI.replace_table[char]
            else:
                replace_char = char
            if replace_char:
                converted_word += replace_char
        return converted_word

    replace_table = {
        ".": None,
        "?": None,
        "!": None,
        "'": None,
        "(": None,
        ")": None,
        "|": None,
        ",": None,
        "’": None,
        "ʻ": None,
        "%": None,
        '"': None,
        ":": None,
        ";": None,
        "*": None,
        "#": None,
        "/": None,
        " ": None,
        "-": None,
        "–": None,
        "Ǎ": "A",
        "Ă": "A",
        "Ä": "A",
        "À": "A",
        "Å": "A",
        "Â": "A",
        "Á": "A",
        "Ã": "A",
        "Č": "C",
        "Ç": "C",
        "É": "E",
        "È": "E",
        "Ê": "E",
        "Ē": "E",
        "Ė": "E",
        "Ë": "E",
        "Ě": "E",
        "Í": "I",
        "İ": "I",
        "Ì": "I",
        "Î": "I",
        "Ï": "I",
        "Ī": "I",
        "Ї": "I",
        "Ł": "L",
        "Ñ": "N",
        "Ń": "N",
        "Ň": "N",
        "Ö": "O",
        "Ø": "O",
        "Ó": "O",
        "Ô": "O",
        "Ộ": "O",
        "Ò": "O",
        "Ō": "O",
        "Ş": "S",
        "Ś": "S",
        "Š": "S",
        "Ș": "S",
        "Ü": "U",
        "Ú": "U",
        "Û": "U",
        "Ý": "Y",
        "Ÿ": "Y",
        "Ž": "Z",
        "Ż": "Z",
        "Ź": "Z",
    }
