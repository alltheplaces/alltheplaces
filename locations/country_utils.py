import unicodedata
from urllib.parse import urlparse

import geonamescache
from babel import Locale, UnknownLocaleError


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


class CountryUtils:
    def __init__(self):
        self.gc = geonamescache.GeonamesCache()

    # All keys in this dict should be lower case. The idea is also that we
    # only place totally non contentious common mappings here.
    UNHANDLED_COUNTRY_MAPPINGS = {
        "espana": "ES",
        "great britain": "GB",
        "england": "GB",
        "scotland": "GB",
        "wales": "GB",
        "northern ireland": "GB",
        "uk": "GB",
        "norge": "NO",
        "united states of america": "US",
        "luxemburg (groothertogdom)": "LU",
        "belgie": "BE",
        "u s a": "US",
    }

    def to_iso_alpha2_country_code(self, country_str):
        """
        Map country string to an ISO alpha-2 country string. This method understands
        ISO alpha-3 to ISO alpha-2 mapping. It also copes with a few common non
        contentious mappings such as "UK" -> "GB", "United Kingdom." -> "GB"
        :param country_str: the string to map to an ISO alpha-2 country code
        :return: ISO alpha-2 country code or None if no clean mapping
        """
        if not country_str:
            return None
        # Clean up some common appendages we see on country strings.
        country_str = strip_accents(country_str.replace(".", "").strip())
        if len(country_str) < 2:
            return None
        if len(country_str) == 2:
            # Check for the clean/fast path, spider has given us a 2-alpha iso country code.
            if self.gc.get_countries().get(country_str.upper()):
                return country_str.upper()
        if len(country_str) == 3:
            # Check for a 3-alpha code, this is done by iteration.
            country_str = country_str.upper()
            for country in self.gc.get_countries().values():
                if country["iso3"] == country_str:
                    return country["iso"]
        # Failed so far, now let's try a match by name.
        country_name = country_str.lower()
        for country in self.gc.get_countries().values():
            if country["name"].lower() == country_name:
                return country["iso"]
        # Finally let's go digging in the random country string collection!
        return self.UNHANDLED_COUNTRY_MAPPINGS.get(country_name)

    def _convert_to_iso2_country_code(self, splits):
        if len(splits) > 0 and len(splits[-1]) == 2:
            candidate = splits[-1].upper()
            if self.gc.get_countries().get(candidate):
                return candidate
            if candidate == "UK":
                return "GB"
        return None

    def country_code_from_spider_name(self, spider_name):
        if isinstance(spider_name, str):
            splits = [split for split in spider_name.split("_") if len(split) == 2]
            if len(splits) == 1:  # Skip multiple countries e.g. homebase_gb_ie
                return self._convert_to_iso2_country_code(splits)
        return None

    def country_code_from_url(self, url):
        if isinstance(url, str):
            return self._convert_to_iso2_country_code(urlparse(url).netloc.split("."))
        return None


def get_locale(country_code: str) -> str | None:
    """
    Get language locale for a given country code.
    :param country_code: ISO alpha-2 country code
    :return: language locale in format of en-US or None if not found
    """
    try:
        locale = Locale.parse("und-" + country_code, sep="-")
        return "-".join(filter(None, [locale.language, locale.territory]))
    except (ValueError, UnknownLocaleError):
        return None
