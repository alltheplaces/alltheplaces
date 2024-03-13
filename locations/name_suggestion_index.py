import requests


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


# This is a lazy initialised singleton as it pulls (over the network) quite a lot of data into memory.
class NSI(metaclass=Singleton):
    """
    Interact with Name Suggestion Index (NSI). The NSI people publish a JSON version of their database
    which is used by the OSM editor to do rather useful brand suggestions when editing POIs.
    """

    def __init__(self):
        self.loaded = False
        self.wikidata_json = None
        self.nsi_json = None

    @staticmethod
    def _request_file(file):
        resp = requests.get("https://raw.githubusercontent.com/osmlab/name-suggestion-index/main/" + file)
        if not resp.status_code == 200:
            raise Exception("NSI load failure")
        return resp.json()

    def _ensure_loaded(self):
        if not self.loaded:
            self.wikidata_json = self._request_file("dist/wikidata.min.json")["wikidata"]
            self.nsi_json = self._request_file("dist/nsi.min.json")["nsi"]
            self.loaded = True

    def lookup_wikidata(self, wikidata_code):
        """
        Lookup wikidata code in the NSI.
        :param wikidata_code: wikidata code to lookup in the NSI
        :return: NSI wikidata.json entry if present
        """
        self._ensure_loaded()
        return self.wikidata_json.get(wikidata_code)

    def iter_wikidata(self, fuzzy_label=None):
        """
        Lookup by fuzzy label match in the NSI.
        :param fuzzy_label: string to fuzzy match
        :return: iterator of matching NSI wikidata.json entries
        """
        self._ensure_loaded()
        s = NSI.normalise(fuzzy_label)
        for k, v in self.wikidata_json.items():
            if not fuzzy_label:
                yield k, v
                continue
            if label := v.get("label"):
                if s in NSI.normalise(label):
                    yield k, v

    def iter_nsi(self, wikidata_code=None):
        """
        Iterate NSI for all items in nsi.json with a matching wikidata code
        :param wikidata_code: wikidata code to match, if None then all entries
        :return: iterator of matching NSI nsi.json item entries
        """
        self._ensure_loaded()
        for v in self.nsi_json.values():
            for item in v["items"]:
                if not wikidata_code:
                    yield item
                elif wikidata_code == item["tags"].get("brand:wikidata"):
                    yield item
                elif wikidata_code == item["tags"].get("operator:wikidata"):
                    yield item

    @staticmethod
    def normalise(s):
        """
        Help fuzzy matcher by "normalising" string data.
        :param s: string to be cleaned
        :return: the cleaned string
        """
        if not s:
            return None
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
