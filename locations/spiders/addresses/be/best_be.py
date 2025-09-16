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
    name = "best_addresses_be"
    item_attributes = {"country": "BE"}
    start_urls = ["data:,"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 300}

    region_urls = [
        "https://opendata.bosa.be/download/best/openaddress-bevlg.zip",  # Flanders
        "https://opendata.bosa.be/download/best/openaddress-bebru.zip",  # Brussels
        "https://opendata.bosa.be/download/best/openaddress-bewal.zip",  # Wallonia
    ]

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
                                yield from self.parse_csv_file(csvf, region_name)

    def parse_csv_file(self, csvfile: IO[bytes], region_name: str) -> Iterable[Feature]:

        text_file = TextIOWrapper(csvfile, encoding="utf-8")

        for row in csv.DictReader(text_file):
            if row.get("status") != "current":
                self.crawler.stats.inc_value(f"{self.name}/skipped_inactive_addresses")
                continue

            item = DictParser.parse(row)

            item["ref"] = row.get("address_id")
            item["lat"] = row.get("EPSG:4326_lat")
            item["lon"] = row.get("EPSG:4326_lon")

            house_number = row.get("house_number", "").strip()
            box_number = row.get("box_number", "").strip()

            if house_number and box_number:
                item["housenumber"] = f"{house_number}/{box_number}"
            elif house_number:
                item["housenumber"] = house_number
            elif box_number:
                item["housenumber"] = box_number

            item["postcode"] = row.get("postcode")

            item["extras"] = {
                "municipality_id": row.get("municipality_id"),
                "street_id": row.get("street_id"),
                "region_code": row.get("region_code"),
                "addr:city:nl": row.get("municipality_name_nl"),
                "addr:city:fr": row.get("municipality_name_fr"),
                "addr:city:de": row.get("municipality_name_de"),
                "addr:street:nl": row.get("streetname_nl"),
                "addr:street:fr": row.get("streetname_fr"),
                "addr:street:de": row.get("streetname_de"),
                "addr:postname:nl": row.get("postname_nl"),
                "addr:postname:fr": row.get("postname_fr"),
            }

            yield item
