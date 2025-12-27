import argparse
import json
import multiprocessing
import os
import pprint
import re
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


@dataclass
class WikidataRecord:
    code: str
    osm_count: int = 0
    nsi_brand: str | None = None
    q_title: str | None = None
    q_description: str | None = None
    atp_count: int = 0
    atp_brand: str | None = None
    atp_supplier_count: set[str] = field(default_factory=set)
    # country -> spider -> count
    atp_splits: dict[str, dict[str, int]] = field(default_factory=dict)

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
            while True:
                if line := stream.readline():
                    yield json.loads(line)
                    continue
                return
        yield from ijson.items(stream, "features.item", use_float=True)
    except Exception as e:
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


def build_file_list(paths: list[str], ignore_spiders: list[str]) -> list[str]:
    """
    Given a list of file and directory paths, traverse it and build a flat list of files.
    Zero length files and files from ignore_spiders list are skipped.
    """
    file_list: list[str] = []
    for p in [Path(path) for path in paths]:
        if p.is_file():
            file_list.append(str(p))
        elif p.is_dir():
            for child in p.iterdir():
                if child.is_file():
                    file_list.append(str(child))
        else:
            raise UsageError(f"no such file or directory: {p}")

    file_list = [f for f in file_list if not ignore_file(f, ignore_spiders) and os.path.getsize(f) > 0]
    if not file_list:
        raise UsageError("no non-empty JSON/ZIP files found")

    return file_list


def ignore_file(s: str, ignore_spiders: list[str]) -> bool:
    if s.endswith(("json", ".zip")):
        return any(ignore_spider in s for ignore_spider in ignore_spiders)
    return True


def get_brand_name(tags: dict) -> str | None:
    """Extract brand name, preferring English."""
    return tags.get("brand:en") or tags.get("brand")


def count_brands_in_file(args_tuple: tuple[str, dict, list[str]]) -> dict[str, WikidataRecord]:
    """
    Count brand occurrences in a single file (worker function for multiprocessing).
    Returns dict of wikidata code -> WikidataRecord.
    """
    file_path, nsi_brands, ignore_spiders = args_tuple
    records: dict[str, WikidataRecord] = {}

    for feature in iter_features([file_path], ignore_spiders):
        properties = feature["properties"]
        wikidata_code = properties.get("brand:wikidata")
        if not wikidata_code:
            continue

        # Get or create record for this wikidata code
        record = records.setdefault(wikidata_code, WikidataRecord(wikidata_code))

        # Update NSI brand if available
        if nsi_id := properties.get("nsi_id"):
            record.nsi_brand = nsi_brands.get(nsi_id)

        # Update counts and brand
        record.atp_count += 1
        if brand := get_brand_name(properties):
            record.atp_brand = brand

        # Update country/spider breakdown - using nested dict directly!
        country = properties.get("addr:country")
        spider = properties.get("@spider")
        record.atp_supplier_count.add(spider)

        if country not in record.atp_splits:
            record.atp_splits[country] = {}
        record.atp_splits[country][spider] = record.atp_splits[country].get(spider, 0) + 1

    return records


def merge_records(dest: dict[str, WikidataRecord], src: dict[str, WikidataRecord]) -> None:
    """Merge wikidata records from src into dest."""
    for code, src_record in src.items():
        if code not in dest:
            dest[code] = src_record
            continue

        dest_record = dest[code]
        # Copy brand info (last one wins, all should be same)
        dest_record.nsi_brand = src_record.nsi_brand
        dest_record.atp_brand = src_record.atp_brand

        # Merge counts
        dest_record.atp_count += src_record.atp_count
        dest_record.atp_supplier_count.update(src_record.atp_supplier_count)

        # Merge nested atp_splits
        for country, spiders in src_record.atp_splits.items():
            if country not in dest_record.atp_splits:
                dest_record.atp_splits[country] = {}
            for spider, count in spiders.items():
                dest_record.atp_splits[country][spider] = dest_record.atp_splits[country].get(spider, 0) + count


def load_osm_and_nsi_data() -> dict[str, WikidataRecord]:
    """Load reference data from OSM taginfo and NSI."""
    records: dict[str, WikidataRecord] = {}

    # Load OSM brand:wikidata tag counts
    re_qcode = re.compile(r"^Q\d+")
    osm_url = "https://taginfo.openstreetmap.org/api/4/key/values?key=brand%3Awikidata&filter=all&lang=en&sortname=count&sortorder=desc&page={}&rp=999&qtype=value"

    for page in range(1, 1000):
        response = requests.get(osm_url.format(page), headers={"User-Agent": BOT_USER_AGENT_REQUESTS})
        if response.status_code != 200:
            raise Exception("Failed to load OSM wikidata tag statistics")

        entries = response.json()["data"]
        if not entries:
            break

        for entry in entries:
            if re_qcode.match(entry["value"]):
                code = entry["value"]
                records.setdefault(code, WikidataRecord(code)).osm_count = entry["count"]

    # Load NSI wikidata labels/descriptions
    nsi = NSI()
    for code, data in nsi.iter_wikidata():
        record = records.setdefault(code, WikidataRecord(code))
        record.q_title = data.get("label", "NO NSI LABEL!")
        record.q_description = data.get("description", "NO NSI DESC!")

    return records


def build_nsi_id_to_brand() -> dict:
    """Build lookup from NSI ID to brand name."""
    nsi = NSI()
    return {item["id"]: brand for item in nsi.iter_nsi() if (brand := get_brand_name(item.get("tags", {})))}


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
            help="Number of CPUs to use when analyzing atp-nsi-osm",
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
            self.analyze_atp_nsi_osm(args, opts)
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
        :param workers: number of parallel workers to use
        :param outfile: JSON result file name to write
        """
        # Load reference data
        nsi_brands = build_nsi_id_to_brand()
        all_records = load_osm_and_nsi_data()

        # Process ATP files in parallel
        workers = opts.workers or multiprocessing.cpu_count()
        files = build_file_list(args, opts.filter_spiders)
        tasks = [(file, nsi_brands, opts.filter_spiders) for file in files]

        with multiprocessing.Pool(workers) as pool:
            results = pool.map(count_brands_in_file, tasks)

        # Merge results from all workers
        for file_records in results:
            merge_records(all_records, file_records)

        # Write output
        output = {"data": [record.to_dict() for record in all_records.values()]}
        with open(opts.outfile, "w") as f:
            json.dump(output, f)

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
