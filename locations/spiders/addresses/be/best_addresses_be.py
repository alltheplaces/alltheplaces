import csv
import shutil
from io import TextIOWrapper
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import IO, Iterable
from zipfile import ZipFile

import requests
import requests_cache
from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.dict_parser import DictParser
from locations.items import Feature


class BeSTAddressesBESpider(AddressSpider):
    item_attributes = {"country": "BE"}
    start_urls = ["data:,"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 300}

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        for url in self.region_urls:
            region_name = url.split("openaddress-")[1].replace(".zip", "")
            self.logger.info(f"Processing region: {region_name}")

            with TemporaryDirectory() as tmp_dir:
                with requests_cache.disabled():
                    with requests.get(url, stream=True) as r:
                        filepath = Path(tmp_dir) / f"{region_name}.zip"
                        with open(filepath, "wb") as f:
                            shutil.copyfileobj(r.raw, f)

                if int(r.headers["Content-Length"]) != filepath.stat().st_size:
                    raise Exception("Incomplete download")

                with ZipFile(filepath, "r") as zip_ref:
                    for csv_file in zip_ref.namelist():
                        if csv_file.endswith(".csv"):
                            self.logger.info(f"Processing CSV file: {csv_file}")
                            with zip_ref.open(csv_file, "r") as csvf:
                                yield from self.parse_csv_file(csvf)

    def parse_csv_file(self, csvfile: IO[bytes]) -> Iterable[Feature]:
        text_file = TextIOWrapper(csvfile, encoding="utf-8")

        for row in csv.DictReader(text_file):
            if row.get("status") != "current":
                self.crawler.stats.inc_value(f"{self.name}/skipped_status/{row.get('status')}")
                continue

            item = DictParser.parse(row)

            item["ref"] = row.get("address_id")
            item["lat"] = row.get("EPSG:4326_lat")
            item["lon"] = row.get("EPSG:4326_lon")
            item["state"] = row.get("region_code")

            item["extras"] = {
                # IDs
                "ref:BE:best_municipality": row.get("municipality_id"),
                "ref:BE:best_street": row.get("street_id"),
                "addr:unit": row.get("box_number"),
                # Multilingual fields
                "addr:city:nl": row.get("municipality_name_nl"),
                "addr:city:fr": row.get("municipality_name_fr"),
                "addr:city:de": row.get("municipality_name_de"),
                "addr:street:nl": row.get("streetname_nl"),
                "addr:street:fr": row.get("streetname_fr"),
                "addr:street:de": row.get("streetname_de"),
                "addr:district:nl": row.get("postname_nl"),
                "addr:district:fr": row.get("postname_fr"),
            }
            yield self.post_process_item(item, row)

    def post_process_item(self, item: Feature, row: dict) -> Iterable[Feature]:
        """Override for custom actions on items"""
        return item
