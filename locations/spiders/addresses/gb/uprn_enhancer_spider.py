import csv
import shutil
from pathlib import Path
from typing import Any, AsyncIterator, Self

import duckdb
import requests
import requests_cache
from scrapy import Request
from scrapy.crawler import Crawler
from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature

# Uses OS Open UPRN and ONS UPRN Directory to add coords and postcodes
# https://osdatahub.os.uk/downloads/open/OpenUPRN
# https://www.ons.gov.uk/methodology/geography/geographicalproducts/nationalstatisticsaddressproducts


class UprnEnhancerSpider(AddressSpider):
    custom_settings = {"DOWNLOAD_TIMEOUT": 60 * 5}

    onsud_region: str = "*"  # ONSUD region file suffix, e.g. "NW"
    postal_towns = {}
    connection = None

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        with open("locations/spiders/addresses/gb/postal_cities.csv") as f:
            for r in csv.DictReader(f):
                spider.postal_towns[r["Outward Code"]] = r["addr:city"]
        return spider

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            "https://hub.arcgis.com/api/search/v1/collections/all/items?limit=1&q=PRD_ONSUD&sortBy=-properties.created",
            callback=self.fetch_uprn_lookup,
        )

    def fetch_uprn_lookup(self, response: Response, **kwargs: Any) -> Any:
        assert response.json()["features"][0]["properties"]["title"].startswith("ONS UPRN Directory (")
        root = Path(self.settings["FILES_STORE"] or "/tmp/atp") / self.name
        root.mkdir(exist_ok=True, parents=True)

        with requests_cache.disabled():
            for url, file_name in [
                (
                    "https://api.os.uk/downloads/v1/products/OpenUPRN/downloads?area=GB&format=CSV&redirect",
                    "OpenUPRN.zip",
                ),
                (
                    "https://www.arcgis.com/sharing/rest/content/items/{}/data".format(
                        response.json()["features"][0]["properties"]["id"]
                    ),
                    "ONS-NSUL.zip",
                ),
            ]:
                local_filepath = root / file_name
                if local_filepath.exists():
                    continue

                with requests.get(url, stream=True) as r:
                    self.logger.info("Downloading: {}".format(file_name))
                    with open(local_filepath, "wb") as f:
                        shutil.copyfileobj(r.raw, f)

        self.connection = duckdb.connect(root / "temp")
        self.connection.execute("INSTALL zipfs FROM community; LOAD zipfs;")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS uprn AS SELECT * FROM 'zip://{}/OpenUPRN.zip/osopenuprn_*.csv';".format(root)
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS uprn2postcode AS SELECT UPRN AS uprn, PCDS AS postcode FROM 'zip://{}/ONS-NSUL.zip/Data/ONSUD_*_{}.csv';".format(
                root, self.onsud_region
            )
        )

        for url in self.start_urls:
            yield Request(url)

    def apply_uprn(self, item: Feature, uprn: int | str) -> None:
        item["extras"]["ref:GB:uprn"] = str(uprn)

        cursor = self.connection.execute("SELECT LATITUDE, LONGITUDE FROM uprn WHERE UPRN = ? LIMIT 1;", [uprn])
        if coords := cursor.fetchone():
            item["lat"], item["lon"] = coords
            # item["extras"]["source:geometry"] = "OS Open UPRN"

        cursor = self.connection.execute("SELECT TRIM(postcode) FROM uprn2postcode WHERE uprn = ? LIMIT 1;", [uprn])
        if pc := cursor.fetchone():
            item["postcode"] = pc[0]
            # item["extras"]["source:addr:postcode"] = "ONSUD"
