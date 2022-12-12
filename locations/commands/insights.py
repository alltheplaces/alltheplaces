import json
import os
from collections import Counter

import requests
from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError

from locations.country_utils import CountryUtils
from locations.name_suggestion_index import NSI


def iter_features(files_and_dirs):
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
    file_list = list(filter(lambda f: f.endswith("json") and os.path.getsize(f) > 0, file_list))
    if len(file_list) == 0:
        raise UsageError("no non-empty JSON files found")
    for file_path in file_list:
        with open(file_path) as f:
            try:
                yield from json.load(f)["features"]
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
        parser.add_argument(
            "--atp-nsi-osm",
            dest="atp_nsi_osm",
            action="store_true",
            help="Cross reference ATP, NSI/WIKIDATA and OSM with each other",
        )
        parser.add_argument(
            "--outfile",
            dest="outfile",
            metavar="OUTFILE",
            default="/tmp/out.json",
            help="Write result of run to file",
        )

    def run(self, args, opts):
        if len(args) < 1:
            raise UsageError()
        if opts.country_codes:
            self.check_country_codes(args)
            return
        if opts.wikidata_codes:
            self.check_wikidata_codes(args)
            return
        if opts.atp_nsi_osm:
            self.analyze_atp_nsi_osm(args, opts.outfile)
            return

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
        for feature in iter_features(args):
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
        for feature in iter_features(args):
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

    def analyze_atp_nsi_osm(self, args, outfile):
        """
        Trawl ATM, NSI and OSM for per wikidata code information.
        :param args: ATP output GeoJSON files / directories to load
        :param outfile: JSON result file name to write
        """

        def lookup_code(wikidata_code):
            # Return record for a wikidata code, adding it to dict if not already present.
            if record := wikidata_dict.get(wikidata_code):
                return record
            record = {
                "code": wikidata_code,
                "osm_count": 0,
                "nsi_brand": None,
                "nsi_description": None,
                "atp_count": None,
                "atp_brand": None,
            }
            wikidata_dict[wikidata_code] = record
            return record

        # A dict keyed by wikidata code.
        wikidata_dict = {}

        # First data set to merge into the output table is wikidata tag count info from OSM.
        osm_url = "https://taginfo.openstreetmap.org/api/4/key/values?key=brand%3Awikidata&filter=all&lang=en&sortname=count&sortorder=desc&page=1&rp=000&qtype=value"
        response = requests.get(osm_url)
        if not response.status_code == 200:
            raise Exception("Failed to load OSM wikidata tag statistics")
        for r in response.json()["data"]:
            lookup_code(r["value"])["osm_count"] = r["count"]

        # Now load each wikidata entry in the NSI dataset and merge into our wikidata table.
        nsi = NSI()
        for k, v in nsi.iter_wikidata():
            r = lookup_code(k)
            r["nsi_brand"] = v.get("label", "NO NSI LABEL!")
            r["nsi_description"] = v.get("description", "NO NSI DESC!")

        # TODO: Could go through ATP spiders themselves looking for Q-codes. Add an atp_count=-1
        #       which would be written over if a matching POI had been scraped by the code below.
        #       If not then that would be a possible problem to highlight.

        # Walk through the referenced ATP downloads, if they have wikidata codes then update our output table.
        for feature in iter_features(args):
            brand_wikidata = feature["properties"].get("brand:wikidata")
            brand = feature["properties"].get("brand")
            if not brand_wikidata:
                continue
            r = lookup_code(brand_wikidata)
            count = r.get("atp_count")
            if not count:
                count = 0
            r["atp_count"] = count + 1
            if brand:
                r["atp_brand"] = brand

        # Write a JSON format output file which is datatables friendly.
        for_datatables = {"data": list(wikidata_dict.values())}
        with open(outfile, "w") as f:
            json.dump(for_datatables, f)
