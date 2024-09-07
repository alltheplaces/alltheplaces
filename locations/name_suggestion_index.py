import re
from urllib.parse import urlparse

import pycountry
import requests
import tldextract
from unidecode import unidecode


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

    def get_wikidata_code_from_url(self, url: str = None) -> str | None:
        """
        Attempt to return a single Wikidata code corresponding to
        the brand or operator of the supplied URL.
        :param_url: URL to find the corresponding Wikidata code for
        :return: Wikidata code, or None if no match found
        """
        self._ensure_loaded()
        supplied_url_domain = urlparse(url).netloc
        # First attempt to find an extact FQDN match
        for wikidata_code, org_parameters in self.wikidata_json.items():
            for official_website in org_parameters.get("officialWebsites", []):
                official_website_domain = urlparse(official_website).netloc
                if official_website_domain == supplied_url_domain:
                    return wikidata_code
        # Next attempt to find an exact match excluding any "www." prefix
        for wikidata_code, org_parameters in self.wikidata_json.items():
            for official_website in org_parameters.get("officialWebsites", []):
                official_website_domain = urlparse(official_website).netloc
                if official_website_domain.lstrip("www.") == supplied_url_domain.lstrip("www."):
                    return wikidata_code
        # Last attempt to find a fuzzy match for registered domain (exlcuding subdomains)
        for wikidata_code, org_parameters in self.wikidata_json.items():
            for official_website in org_parameters.get("officialWebsites", []):
                official_website_reg = tldextract.extract(official_website).registered_domain
                supplied_url_reg = tldextract.extract(supplied_url_domain).registered_domain
                if official_website_reg == supplied_url_reg:
                    return wikidata_code
        return None

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

    def iter_country(self, country_code=None):
        """
        Lookup by country code match in the NSI.
        :param country_code: 2-letter country code to search for
        :return: iterator of matching NSI wikidata.json entries
        """
        self._ensure_loaded()
        for v in self.nsi_json.values():
            for item in v["items"]:
                if not country_code:
                    yield item
                elif country_code.lower() in item["locationSet"].get("include"):
                    yield item

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

    def generate_keys_from_nsi_attributes(nsi_attributes: dict) -> tuple[str, str] | None:
        """
        From supplied NSI attributes of a brand or operator, generate a tuple
        containing:
          1. Key suitable for use as a spider key and filename.
          2. Class name suitable for use as the name of a spider class.
        If the brand or operator exists in one
        or two countries, add ISO 3166-1 alpha-2 codes for the one or two
        countries as suffixes to the generated key.
        :param nsi_attributes: dictionary of NSI attributes for a brand or
                               operator.
        :return: generated key or None if a key could not be generated.
        """
        key = None

        # Try using the NSI "name" field and if that doesn't work, try the
        # NSI "displayName" field instead.
        if nsi_attributes.get("tags") and nsi_attributes["tags"].get("name"):
            key = re.sub(
                r"_+",
                "_",
                re.sub(r"[^\w ]", "", unidecode(nsi_attributes["tags"]["name"]).replace("&", "and").lower())
                .strip()
                .replace(" ", "_"),
            )
            class_name = (
                re.sub(r"[^\w]", "", unidecode(nsi_attributes["tags"]["name"]).replace("&", "And"))
                .strip()
                .replace(" ", "")
            )
        if not key and nsi_attributes.get("displayName"):
            key = re.sub(
                r"_+",
                "_",
                re.sub(r"[^\w ]", "", unidecode(nsi_attributes["displayName"]).replace("&", "and").lower())
                .strip()
                .replace(" ", "_"),
            )
            class_name = (
                re.sub(r"[^\w]", "", unidecode(nsi_attributes["displayName"]).replace("&", "And"))
                .strip()
                .replace(" ", "")
            )
        if not key or not class_name:
            return None

        # Add country suffix(es) if the brand/operator is in one or two
        # countries. If the brand/operator is in three or more countries, do
        # not add a country suffix(es) as the key/class name will be too long.
        if nsi_attributes.get("locationSet") and nsi_attributes["locationSet"].get("include"):
            if len(nsi_attributes["locationSet"]["include"]) == 1 or len(nsi_attributes["locationSet"]["include"]) == 2:
                for country_code in nsi_attributes["locationSet"]["include"]:
                    if not pycountry.countries.get(alpha_2=country_code.upper()):
                        continue
                    key = f"{key}_{country_code.lower()}"
                    class_name = f"{class_name}{country_code.upper()}"

        class_name = f"{class_name}Spider"
        return (key, class_name)

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
