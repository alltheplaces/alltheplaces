import json
import geonamescache
import os
import requests
from collections import Counter
from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError


def feature_iter(files_and_dirs):
    """
    Iterate through a set of GeoJSON files and directories. Each item in the iteration is a
    single feature. Zero length files are skipped. Only files ending .json or .geojson are
    processed.

    :param files_and_dirs: a list of files and directories
    :return: a GeoJSON feature iterator
    """
    file_list = []
    for file_or_dir in files_and_dirs:
        if os.path.isfile(file_or_dir):
            file_list.append(file_or_dir)
        elif os.path.isdir(file_or_dir):
            for file_name in os.listdir(file_or_dir):
                file_list.append(os.path.abspath(os.path.join(file_or_dir, file_name)))
        else:
            raise UsageError("no such file or directory: " + file_or_dir)
    file_list = list(
        filter(lambda f: f.endswith("json") and os.path.getsize(f) > 0, file_list)
    )
    if len(file_list) == 0:
        raise UsageError("no non-empty JSON files found")
    for file_path in file_list:
        with open(file_path, "r") as f:
            try:
                for feature in json.load(f)["features"]:
                    yield feature
            except Exception as e:
                print("Failed to decode: " + file_path)
                print(e)


# Some utilities that help with the analysis of project GeoJSON output files.
class InsightsCommand(ScrapyCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self):
        return "[options] <file/dir> ... <file/dir>"

    def short_desc(self):
        return "Analyze GeoJSON POI files for quality insights"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_argument(
            "--country-codes",
            dest="country_codes",
            action="store_true",
            help="Look at country code values, are they present? do they map to an ISO alpha code cleanly?",
        )
        parser.add_argument(
            "--wikidata-codes",
            dest="wikidata_codes",
            action="store_true",
            help="Are the wikidata codes in the GeoJSON known to NSI / sensible?",
        )

    def run(self, args, opts):
        if len(args) < 1:
            raise UsageError()
        if opts.country_codes:
            self.check_country_codes(args)
        if opts.wikidata_codes:
            self.check_wikidata_codes(args)

    def show_counter(self, msg, counter):
        if len(counter.most_common()) > 0:
            print(msg)
            print(counter)

    def check_country_codes(self, args):
        country_utils = CountryUtils()
        country_clean_counter = Counter()
        invalid_country_counter = Counter()
        spider_failed_counter = Counter()
        spider_missing_counter = Counter()
        fixed_country_counter = Counter()
        country_counter = Counter()
        for feature in feature_iter(args):
            spider_name = feature["properties"].get("@spider")
            country = feature["properties"].get("addr:country")
            if country:
                mapped = country_utils.to_iso_alpha2_country_code(country)
                if not mapped:
                    invalid_country_counter[country] += 1
                    spider_failed_counter[spider_name] += 1
                    continue
                if mapped == country:
                    country_clean_counter[country] += 1
                else:
                    fixed_country_counter[country + " -> " + mapped] += 1
                country_counter[mapped] += 1
            else:
                spider_missing_counter[spider_name] += 1
        self.show_counter("ORIGINAL CLEAN COUNTRY CODES:", country_clean_counter)
        self.show_counter("MAPPED/FIXED COUNTRY CODES:", fixed_country_counter)
        self.show_counter("CLEAN/MAPPED COUNTRY CODES:", country_counter)
        self.show_counter("INVALID COUNTRY CODES:", invalid_country_counter)
        self.show_counter("NO COUNTRY CODE SUPPLIED BY SPIDER:", spider_missing_counter)
        self.show_counter("INVALID COUNTRY CODES BY SPIDER:", spider_failed_counter)

    def check_wikidata_codes(self, args):
        nsi = NSI()
        spider_empty_counter = Counter()
        spider_nsi_missing_counter = Counter()
        for feature in feature_iter(args):
            spider_name = feature["properties"].get("@spider")
            brand_wikidata = feature["properties"].get("brand:wikidata")
            if not brand_wikidata:
                spider_empty_counter[spider_name] += 1
            elif not nsi.lookup_wikidata(brand_wikidata):
                spider_nsi_missing_counter[spider_name + "/" + brand_wikidata] += 1
            else:
                # TODO: query wikidata to see if Q-code remotely sensible?
                pass
        self.show_counter("SPIDERS WITH NO BRAND DATA:", spider_empty_counter)
        self.show_counter("NSI MISSING WIKIDATA CODE:", spider_nsi_missing_counter)


class NSI(object):
    """
    Interact with Name Suggestion Index (NSI). The NSI distribution is a GIT sub-module of this
    project. As part of their GIT repo the NSI people publish a JSON version of their database
    which is used by the OSM editor to do rather useful brand suggestions when editing POIs.
    """

    def __init__(self):
        self.nsi_wikidata = None

    def _ensure_loaded(self):
        if self.nsi_wikidata is None:
            resp = requests.get("https://raw.githubusercontent.com/osmlab/name-suggestion-index/main/dist/wikidata.min.json")
            self.nsi_wikidata = resp.json()["wikidata"]
            if not self.nsi_wikidata:
                self.nsi_wikidata = {}

    def lookup_wikidata(self, brand_wikidata):
        self._ensure_loaded()
        return self.nsi_wikidata.get(brand_wikidata)


class CountryUtils(object):
    def __init__(self):
        self.gc = geonamescache.GeonamesCache()

    # All keys in this dict should be lower case. The idea is also that we
    # only place totally non contentious common mappings here.
    UNHANDLED_COUNTRY_MAPPINGS = {
        "espana": "ES",
        "great britain": "GB",
        "norge": "NO",
        "uk": "GB",
        "united states of america": "US",
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
        country_str = country_str.strip().replace(".", "")
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
