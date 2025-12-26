import argparse
import json
import multiprocessing
import os
import pprint
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Iterable
from zipfile import ZipFile

import ijson
import requests
import scrapy.statscollectors
from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError

from locations.name_suggestion_index import NSI
from locations.user_agents import BOT_USER_AGENT_REQUESTS


def _make_int_defaultdict():
    return defaultdict(int)


@dataclass
class WikidataRecord:
    code: str
    osm_count: int = 0
    nsi_brand: str | None = None
    q_title: str | None = None
    q_description: str | None = None
    atp_count: int = 0
    atp_brand: str | None = None
    atp_country_count: int = 0
    atp_supplier_count: set[str] = field(default_factory=set)
    atp_splits: dict[str, dict[str, int]] = field(default_factory=lambda: defaultdict(_make_int_defaultdict))

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "osm_count": self.osm_count,
            "nsi_brand": self.nsi_brand,
            "q_title": self.q_title,
            "q_description": self.q_description,
            "atp_count": self.atp_count,
            "atp_brand": self.atp_brand,
            "atp_country_count": len(self.atp_splits),
            "atp_supplier_count": len(self.atp_supplier_count),
            "atp_splits": self.atp_splits,
        }


def iter_json(stream: IO[bytes] | IO[str], file_name: str) -> Iterable[dict]:
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


def iter_features(files_and_dirs: list[str], ignore_spiders: list[str]) -> Iterable[dict]:
    """
    Iterate through a set of GeoJSON files and directories. Each item in the iteration is a
    single feature. Zero length files are skipped. Only files ending .json, .geojson or .ndgeojson
    are processed.
    :param files_and_dirs: a list of files and directories
    :param ignore_spiders: file names matching any of the strings in this list will be ignored
    :return: a GeoJSON feature iterator
    """

    file_list = build_file_list(files_and_dirs, ignore_spiders)

    for file_path in file_list:
        if file_path.endswith(".zip"):
            with ZipFile(file_path) as zip_file:
                for name in zip_file.namelist():
                    if not ignore_file(name, ignore_spiders):
                        with zip_file.open(name) as f:
                            yield from iter_json(f, name)
        else:
            with open(file_path) as f:
                yield from iter_json(f, file_path)


def ignore_file(s: str, ignore_spiders: list[str]) -> bool:
    if s.endswith(("json", ".zip")):
        for ignore_spider in ignore_spiders:
            if ignore_spider in s:
                return True
        # It's a JSON or ZIP file whose name does not trigger any ignore filter, it's good to process.
        return False
    else:
        return True


def build_file_list(paths: list[str], ignore_spiders: list[str]) -> list[str]:
    """
    Given a list of file and directory paths, traverse it and build a flat list of files.
    Zero length files and files from ignore_spiders list are skipped.
    """
    file_list: list[Path] = []
    for p in [Path(path) for path in paths]:
        if p.is_file():
            file_list.append(str(p))
        elif p.is_dir():
            for child in p.iterdir():
                if child.is_file():
                    file_list.append(str(child))
        else:
            raise UsageError(f"no such file or directory: {p}")

    file_list = list(filter(lambda x: not ignore_file(x, ignore_spiders) and os.path.getsize(x) > 0, file_list))
    if len(file_list) == 0:
        raise UsageError("no non-empty JSON/ZIP files found")

    return file_list


def lookup_code(wikidata_code: str, wikidata_dict: dict[str, WikidataRecord]) -> WikidataRecord:
    # Return record for a wikidata code, adding it to dict if not already present.
    return wikidata_dict.setdefault(wikidata_code, WikidataRecord(wikidata_code))


def get_brand_name(item_tags: dict) -> str | None:
    # Prefer English brand name for insights application (https://www.alltheplaces.xyz/wikidata.html).
    if brand_en := item_tags.get("brand:en"):
        return str(brand_en)
    if brand := item_tags.get("brand"):
        return str(brand)
    return None


def collect_wikidata_for_file(args_tuple: tuple[str, dict, list[str]]) -> dict[str, WikidataRecord]:
    """
    Collect brand wikidata information from a single ATP output GeoJSON file.
    This function is intended to be called in parallel from multiple processes.
    """
    file_path, nsi_id_to_brand, ignore_spiders = args_tuple

    wikidata_dict: dict[str, WikidataRecord] = {}

    # TODO: Could go through ATP spiders themselves looking for Q-codes. Add an atp_count=-1
    #       which would be written over if a matching POI had been scraped by the code below.
    #       If not then that would be a possible problem to highlight.

    # Walk through the referenced ATP downloads, if they have wikidata codes then update our output table.
    for feature in iter_features([file_path], ignore_spiders):
        properties = feature["properties"]
        brand_wikidata = properties.get("brand:wikidata")
        if not brand_wikidata:
            continue
        brand = get_brand_name(properties)
        r = lookup_code(brand_wikidata, wikidata_dict)

        if nsi_id := properties.get("nsi_id"):
            # If we have found the brand in NSI then show the NSI brand name in the
            # output JSON to help highlight where a spider brand name differs from
            # the NSI brand name.
            r.nsi_brand = nsi_id_to_brand.get(nsi_id)

        r.atp_count += 1
        if brand:
            r.atp_brand = brand

        country = properties.get("addr:country")
        spider = properties.get("@spider")

        r.atp_supplier_count.add(spider)
        r.atp_splits[country][spider] += 1

    return wikidata_dict


def merge_wikidata_dicts(dest: dict[str, WikidataRecord], src: dict[str, WikidataRecord]) -> None:
    """
    Merge wikidata records from src dict into dest dict.
    :param dest: destination wikidata dict
    :param src: source wikidata dict
    """
    for q_code, src_record in src.items():
        dest_record = lookup_code(q_code, dest)
        dest_record.nsi_brand = src_record.nsi_brand
        dest_record.atp_brand = src_record.atp_brand
        dest_record.atp_count += src_record.atp_count
        dest_record.atp_supplier_count.update(src_record.atp_supplier_count)

        # Merge the atp_splits structure.
        for country, src_splits in src_record.atp_splits.items():
            for spider, count in src_splits.items():
                dest_record.atp_splits[country][spider] += count


def build_wikidata_dict() -> dict[str, WikidataRecord]:
    # A dict keyed by wikidata code.
    wikidata_dict = {}

    # First data set to merge into the output table is wikidata tag count info from OSM.
    # There are a lot of unique wikidata codes so use paging on the taginfo service.
    re_qcode = re.compile(r"^Q\d+")
    osm_url_template = "https://taginfo.openstreetmap.org/api/4/key/values?key=brand%3Awikidata&filter=all&lang=en&sortname=count&sortorder=desc&page={}&rp=999&qtype=value"
    for page in range(1, 1000):
        response = requests.get(osm_url_template.format(page), headers={"User-Agent": BOT_USER_AGENT_REQUESTS})
        if not response.status_code == 200:
            raise Exception("Failed to load OSM wikidata tag statistics")
        entries = response.json()["data"]
        if len(entries) == 0:
            # We've run of the end of OSM wikidata entries.
            break
        for r in entries:
            if re_qcode.match(r["value"]):
                lookup_code(r["value"], wikidata_dict).osm_count += r["count"]

    # Now load each wikidata entry in the NSI dataset and merge into our wikidata table.
    nsi = NSI()
    for k, v in nsi.iter_wikidata():
        r = lookup_code(k, wikidata_dict)
        r.q_title = v.get("label", "NO NSI LABEL!")
        r.q_description = v.get("description", "NO NSI DESC!")

    return wikidata_dict


def build_nsi_id_to_brand() -> dict:
    # Build a lookup table from NSI id's to associated brand name if any.
    nsi = NSI()
    nsi_id_to_brand = {}
    for item in nsi.iter_nsi():
        if brand := get_brand_name(item.get("tags", {})):
            nsi_id_to_brand[item["id"]] = brand
    return nsi_id_to_brand


# Some utilities that help with the analysis of project GeoJSON output files.
class InsightsCommand(ScrapyCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self) -> str:
        return "[options] <file/dir> ... <file/dir>"

    def short_desc(self) -> str:
        return "Analyze GeoJSON POI files (including ZIP archives) for quality insights"

    def add_options(self, parser: argparse.ArgumentParser) -> None:
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
            "--nsi-overrides",
            dest="nsi_overrides",
            action="store_true",
            help="Check for feature tags that differ from the brand's NSI preset",
        )
        parser.add_argument(
            "--workers",
            dest="workers",
            type=int,
            default=None,
            help="Number of parallel workers to use when analyzing atp-nsi-osm",
        )

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        if len(args) < 1:
            raise UsageError()
        if opts.value_types:
            self.check_value_types(args, opts)
            return
        if opts.wikidata_codes:
            self.check_wikidata_codes(args, opts)
            return
        if opts.atp_nsi_osm:
            start_time = time.time()
            self.analyze_atp_nsi_osm(args, opts)
            print("ATP-NSI-OSM analysis took {:.2f} seconds".format(time.time() - start_time))
            return
        if opts.nsi_overrides:
            self.nsi_overrides(args, opts)
            return

    def show_counter(self, msg: str, counter: Counter) -> None:
        if len(counter.most_common()) > 0:
            print(msg)
            print(counter)

    def check_value_types(self, args: list[str], opts: argparse.Namespace) -> None:
        stats = scrapy.statscollectors.StatsCollector(self)
        for feature in iter_features(args, opts.filter_spiders):
            spider_name = feature["properties"].get("@spider")
            for k, v in feature["properties"].items():
                if not isinstance(v, str):
                    stats.inc_value(f"{spider_name}/{k}/{type(v).__name__}")

            pprint.pp(stats._stats)

    def check_wikidata_codes(self, args: list[str], opts: argparse.Namespace) -> None:
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

    def analyze_atp_nsi_osm(self, args: list[str], opts: argparse.Namespace) -> None:  # noqa: C901
        """
        Trawl ATP, NSI and OSM for per wikidata code information.
        :param args: ATP output GeoJSON files / directories to load
        :param outfile: JSON result file name to write
        """

        files = build_file_list(args, opts.filter_spiders)
        nsi_id_to_brand = build_nsi_id_to_brand()
        result_wikidata_dict = build_wikidata_dict()

        # Spawn a pool to process each ATP output file in parallel.
        # TODO: revisit default number of workers?
        num_workers = opts.workers or multiprocessing.cpu_count()
        tasks = [(file, nsi_id_to_brand, opts.filter_spiders) for file in files]
        with multiprocessing.Pool(num_workers) as pool:
            results = pool.map(collect_wikidata_for_file, tasks)

        # Merge wikidata dicts from each file into our result.
        for wikidata_dict in results:
            merge_wikidata_dicts(result_wikidata_dict, wikidata_dict)

        # Write a JSON format output file which is datatables friendly.
        for_datatables = {"data": [record.to_dict() for record in result_wikidata_dict.values()]}
        with open(opts.outfile, "w") as f:
            json.dump(for_datatables, f)

    def nsi_overrides(self, args: list[str], opts: argparse.Namespace) -> None:
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
