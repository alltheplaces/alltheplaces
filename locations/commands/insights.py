import json
import os
import pprint
import re
from collections import Counter, defaultdict
from zipfile import ZipFile

import ijson
import requests
import scrapy.statscollectors
from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError

from locations.country_utils import CountryUtils
from locations.name_suggestion_index import NSI


def iter_json(stream, file_name):
    try:
        if file_name.endswith("ndgeojson"):
            # New line delimited GeoJSON is to be read a line at a time.
            while True:
                if line := stream.readline():
                    yield json.loads(line)
                    continue
                return
        # Assume the file is GeoJSON format, further assume many features and stream read the features.
        yield from ijson.items(stream, "features.item", use_float=True)
    except Exception as e:
        # Fail hard (for this file) on the first JSON error we come across.
        print("Failed to decode: " + file_name)
        print(e)


def iter_features(files_and_dirs, ignore_spiders):
    """
    Iterate through a set of GeoJSON files and directories. Each item in the iteration is a
    single feature. Zero length files are skipped. Only files ending .json, .geojson or .ndgeojson
    are processed.
    :param files_and_dirs: a list of files and directories
    :param ignore_spiders: file names matching any of the strings in this list will be ignored
    :return: a GeoJSON feature iterator
    """

    def ignore_file(s):
        if s.endswith("json") or s.endswith(".zip"):
            for ignore_spider in ignore_spiders:
                if ignore_spider in s:
                    return True
            # It's a JSON or ZIP file whose name does not trigger any ignore filter, it's good to process.
            return False
        else:
            return True

    file_list = []
    for file_or_dir in files_and_dirs:
        if os.path.isfile(file_or_dir):
            file_list.append(file_or_dir)
        elif os.path.isdir(file_or_dir):
            for file_name in os.listdir(file_or_dir):
                file_list.append(os.path.abspath(os.path.join(file_or_dir, file_name)))
        else:
            raise UsageError("no such file or directory: " + file_or_dir)

    file_list = list(filter(lambda x: not ignore_file(x) and os.path.getsize(x) > 0, file_list))
    if len(file_list) == 0:
        raise UsageError("no non-empty JSON/ZIP files found")

    for file_path in file_list:
        if file_path.endswith(".zip"):
            with ZipFile(file_path) as zip_file:
                for name in zip_file.namelist():
                    if not ignore_file(name):
                        with zip_file.open(name) as f:
                            yield from iter_json(f, name)
        else:
            with open(file_path) as f:
                yield from iter_json(f, file_path)


# Some utilities that help with the analysis of project GeoJSON output files.
class InsightsCommand(ScrapyCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self):
        return "[options] <file/dir> ... <file/dir>"

    def short_desc(self):
        return "Analyze GeoJSON POI files (including ZIP archives) for quality insights"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_argument(
            "--filter",
            dest="filter_spiders",
            action="append",
            default=[],
            help="Do not process data for spider matching this file name fragment",
        )
        parser.add_argument(
            "--value-types",
            dest="value_types",
            action="store_true",
            help="Check property values are strings",
        )
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
        parser.add_argument(
            "--html-encoding",
            dest="html_encoding",
            action="store_true",
            help="Check fields for html escaped content",
        )
        parser.add_argument(
            "--nsi-overrides",
            dest="nsi_overrides",
            action="store_true",
            help="Check for feature tags that differ from the brand's NSI preset",
        )

    def run(self, args, opts):
        if len(args) < 1:
            raise UsageError()
        if opts.value_types:
            self.check_value_types(args, opts)
            return
        if opts.country_codes:
            self.check_country_codes(args, opts)
            return
        if opts.wikidata_codes:
            self.check_wikidata_codes(args, opts)
            return
        if opts.atp_nsi_osm:
            self.analyze_atp_nsi_osm(args, opts)
            return
        if opts.html_encoding:
            self.check_html_encoding(args, opts)
            return
        if opts.nsi_overrides:
            self.nsi_overrides(args, opts)
            return

    def show_counter(self, msg, counter):
        if len(counter.most_common()) > 0:
            print(msg)
            print(counter)

    def check_value_types(self, args, opts):
        stats = scrapy.statscollectors.StatsCollector(self)
        for feature in iter_features(args, opts.filter_spiders):
            spider_name = feature["properties"].get("@spider")
            for k, v in feature["properties"].items():
                if not isinstance(v, str):
                    stats.inc_value(f"{spider_name}/{k}/{type(v).__name__}")

            pprint.pp(stats._stats)

    def check_country_codes(self, args, opts):
        country_utils = CountryUtils()
        country_clean_counter = Counter()
        invalid_country_counter = Counter()
        spider_failed_counter = Counter()
        spider_missing_counter = Counter()
        fixed_country_counter = Counter()
        country_counter = Counter()
        for feature in iter_features(args, opts.filter_spiders):
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

    def check_wikidata_codes(self, args, opts):
        nsi = NSI()
        spider_empty_counter = Counter()
        spider_nsi_missing_counter = Counter()
        for feature in iter_features(args, opts.filter_spiders):
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

    def check_html_encoding(self, args, opts):
        spider_counter = Counter()
        for feature in iter_features(args, opts.filter_spiders):
            spider_name = feature["properties"]["@spider"]
            for key, value in feature["properties"].items():
                if isinstance(value, str):
                    if re.search(r"&#?\w+;", value):
                        spider_counter[spider_name] += 1
                        break
        self.show_counter("SPIDERS WITH HTML ENCODED OUTPUT:", spider_counter)

    def analyze_atp_nsi_osm(self, args, opts):
        """
        Trawl ATP, NSI and OSM for per wikidata code information.
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
                "q_title": None,
                "q_description": None,
                "atp_count": None,
                "atp_brand": None,
                "atp_country_count": 0,
                "atp_supplier_count": set(),
                "atp_splits": {},
            }
            wikidata_dict[wikidata_code] = record
            return record

        def get_brand_name(item_tags: dict):
            # Prefer English brand name for insights application (https://www.alltheplaces.xyz/wikidata.html).
            return item_tags.get("brand:en") or item_tags.get("brand")

        # A dict keyed by wikidata code.
        wikidata_dict = {}

        # First data set to merge into the output table is wikidata tag count info from OSM.
        # There are a lot of unique wikidata codes so use paging on the taginfo service.
        osm_url_template = "https://taginfo.openstreetmap.org/api/4/key/values?key=brand%3Awikidata&filter=all&lang=en&sortname=count&sortorder=desc&page={}&rp=999&qtype=value"
        for page in range(1, 1000):
            response = requests.get(osm_url_template.format(page))
            if not response.status_code == 200:
                raise Exception("Failed to load OSM wikidata tag statistics")
            entries = response.json()["data"]
            if len(entries) == 0:
                # We've run of the end of OSM wikidata entries.
                break
            for r in entries:
                lookup_code(r["value"])["osm_count"] = r["count"]

        # Now load each wikidata entry in the NSI dataset and merge into our wikidata table.
        nsi = NSI()
        for k, v in nsi.iter_wikidata():
            r = lookup_code(k)
            r["q_title"] = v.get("label", "NO NSI LABEL!")
            r["q_description"] = v.get("description", "NO NSI DESC!")

        # Build a lookup table from NSI id's to associated brand name if any.
        nsi_id_to_brand = {}
        for item in nsi.iter_nsi():
            if brand := get_brand_name(item.get("tags", {})):
                nsi_id_to_brand[item["id"]] = brand

        # TODO: Could go through ATP spiders themselves looking for Q-codes. Add an atp_count=-1
        #       which would be written over if a matching POI had been scraped by the code below.
        #       If not then that would be a possible problem to highlight.

        # Walk through the referenced ATP downloads, if they have wikidata codes then update our output table.
        for feature in iter_features(args, opts.filter_spiders):
            properties = feature["properties"]
            brand_wikidata = properties.get("brand:wikidata")
            if not brand_wikidata:
                continue
            brand = get_brand_name(properties)
            r = lookup_code(brand_wikidata)

            if nsi_id := properties.get("nsi_id"):
                # If we have found the brand in NSI then show the NSI brand name in the
                # output JSON to help highlight where a spider brand name differs from
                # the NSI brand name.
                r["nsi_brand"] = nsi_id_to_brand.get(nsi_id)

            count = r.get("atp_count") or 0
            r["atp_count"] = count + 1
            if brand:
                r["atp_brand"] = brand

            splits = r["atp_splits"]
            country = properties.get("addr:country")
            if country not in splits:
                splits[country] = {}
            split = splits[country]

            spider = properties.get("@spider")
            r["atp_supplier_count"].add(spider)
            spider_count = split.get(spider) or 0
            split[spider] = spider_count + 1

        for record in wikidata_dict.values():
            record["atp_country_count"] = len(record["atp_splits"])
            record["atp_supplier_count"] = len(record["atp_supplier_count"])

        # Write a JSON format output file which is datatables friendly.
        for_datatables = {"data": list(wikidata_dict.values())}
        with open(opts.outfile, "w") as f:
            json.dump(for_datatables, f)

    def nsi_overrides(self, args, opts):
        nsi = NSI()
        nsi._ensure_loaded()
        # Collect category properties like preserveTags for convenience, and create a quick lookup
        # by ID
        nsi_items = {}
        for v in nsi.nsi_json.values():
            for item in v["items"]:
                nsi_items[item["id"]] = item | v["properties"]

        counts = defaultdict(Counter)
        for feature in iter_features(args, opts.filter_spiders):
            properties = feature["properties"]

            if "nsi_id" not in properties:
                continue
            if properties["nsi_id"] not in nsi_items:
                print("No NSI preset with ID", properties["nsi_id"])
                continue

            match = nsi_items[properties["nsi_id"]]
            for key, value in match["tags"].items():
                if properties.get(key) != value and not any(
                    re.match(pat, key) for pat in match.get("preserveTags", [])
                ):
                    counts[key][properties["@spider"]] += 1

        for key, counter in counts.items():
            self.show_counter(f"SPIDERS WITH MISMATCHED {key} TAG:", counter)
