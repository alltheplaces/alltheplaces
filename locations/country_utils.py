import unicodedata
from urllib.parse import urlparse

import geonamescache
import pycountry
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

    def country_code_from_spider_name(self, spider_name: str) -> str | None:
        """
        If a spider name has a single ISO 3166-1 alpha-2 country code in
        lowercase as a suffix, return this country code. For example, in a
        spider name of "example_spider_us", the string "US" is returned as the
        ISO 3166-1 alpha-2 country code. This function returns None in all
        other circumstances including these examples:
          - "example_spider_zz" (invalid ISO 3166-1 alpha-2 country code)
          - "example_spider_uk" (invalid ISO 3166-1 alpha-2 country code)
          - "example_spider_US" (incorrect case in spider name)
          - "example_spider_fr_gb" (more than one country specified)

        Note that "example_spider_zz_us" will return the string "US" because
        there is only one valid ISO 3166-1 alpha-2 country code provided as
        a suffix. The "zz" is ignored.

        :param spider_name: name of an All The Places spider in snake case
        :return: ISO 3166-1 alpha-2 country code as an uppercase string, or
                 None if a single valid ISO 3166-1 alpha-2 country code is not
                 included as a suffix for the provided spider name.
        """
        if isinstance(spider_name, str):
            spider_name_parts = spider_name.split("_")
            country_code_candidates = list(
                map(
                    str.upper,
                    filter(
                        lambda x: len(x) == 2 and x.upper() in [country.alpha_2 for country in pycountry.countries],
                        spider_name_parts,
                    ),
                )
            )
            if len(country_code_candidates) == 1:
                if country_code_candidates[-1].lower() == spider_name_parts[-1]:
                    return country_code_candidates[-1]
            elif len(country_code_candidates) >= 2:
                if country_code_candidates[-1].lower() == spider_name_parts[-1]:
                    if (
                        country_code_candidates[-1].lower() == spider_name_parts[-1]
                        and country_code_candidates[-2].lower() != spider_name_parts[-2]
                    ):
                        return country_code_candidates[-1]
        return None

    def country_code_from_url(self, url: str) -> str | None:
        """
        Return an ISO 3166-1 alpha-2 country code from a URL which contains a
        country code top-level domain (ccTLD). Refer to the full list of
        registered ccTLD at https://www.iana.org/domains/root/db

        :param url: URL to extract an ISO 3166-1 alpha-2 country code from
        :return: ISO 3166-1 alpha-2 country code as an uppercase string, or
                 None if a valid ccTLD is not included in the URL.
        """
        if not isinstance(url, str):
            return None
        if not url.strip():
            return None
        url_domain_parts = urlparse(url).netloc.split(".")
        if len(url_domain_parts) > 0 and len(url_domain_parts[-1]) == 2:
            candidate = url_domain_parts[-1].upper()
            if self.gc.get_countries().get(candidate):
                return candidate
            if candidate == "UK":
                # United Kingdom uses the ccTLD of "UK" but the corresponding
                # ISO 3166-1 alpha-2 code is "GB" for Great Britain.
                return "GB"
            if candidate == "AC":
                # Ascension Island uses the ccTLD of "AC" but the
                # corresponding ISO 3166-1 alpha-2 code is "SH" for Saint
                # Helena, Ascension and Tristan de Cunha.
                return "SH"
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
