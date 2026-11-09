import csv
import re
import shutil
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, Iterator, Self

import duckdb
import openpyxl
import requests
import requests_cache
from scrapy import Request
from scrapy.crawler import Crawler
from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.pipelines.extract_gb_postcode import GB_POSTCODE_PATTERN

# Uses OS Open UPRN and ONS UPRN Directory to add coords and postcodes
# https://osdatahub.os.uk/downloads/open/OpenUPRN
# https://www.ons.gov.uk/methodology/geography/geographicalproducts/nationalstatisticsaddressproducts


class UprnEnhancerSpider(AddressSpider):

    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # FOI, addr+UPRN
        + " Contains OS data © Crown copyright and database right."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # ONSUD, postcodes
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }
    requires_proxy = True
    no_refs = True
    custom_settings = {"DOWNLOAD_TIMEOUT": 60 * 5}

    onsud_region: str = "*"  # ONSUD region file suffix, e.g. "NW"
    postal_towns = {}
    connection = None

    ref_column: str | None = None
    uprn_column: str
    address_columns: list[str]

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

    def iter_rows(self, response: Response) -> Iterator[tuple]:
        if response.url.split("?")[0].lower().endswith(".csv"):
            yield from csv.reader(StringIO(response.body.decode("utf-8-sig", errors="replace")))
        else:
            yield from openpyxl.load_workbook(BytesIO(response.body), read_only=True).active.iter_rows(values_only=True)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        rows = self.iter_rows(response)
        header = next(rows)
        address_re = self.get_regex()

        for row in rows:
            addr = {}
            for k, v in zip(header, row):
                addr[k] = v.strip() if isinstance(v, str) else v

            self.pre_process_data(addr)
            address = merge_address_lines([addr.get(line) for line in self.address_columns])

            item = Feature()
            item["ref"] = str(addr.get(self.ref_column))

            if uprn := addr.get(self.uprn_column):
                self.apply_uprn(item, int(uprn))

            if address_re and (match := address_re.match(address)):
                match_groups = match.groupdict()
                item["street_address"] = match_groups.get("street_address")
                item["extras"]["addr:suburb"] = match_groups.get("suburb")
                item["city"] = match_groups.get("city")
            else:
                item["addr_full"] = address or merge_address_lines(
                    [*GB_POSTCODE_PATTERN.sub("", address).split(","), item.get("postcode"), "United Kingdom"]
                )

            if not item.get("city") and item.get("postcode"):
                item["city"] = self.postal_towns.get(item["postcode"].split(" ", 1)[0])

            yield from self.post_process_item(item, response, addr)

    def get_regex(self) -> re.Pattern | None:
        return None

    def pre_process_data(self, addr: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, addr: dict, **kwargs) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item

    def apply_uprn(self, item: Feature, uprn: int | str) -> None:
        item["extras"]["ref:GB:uprn"] = str(uprn)

        if not self.connection:
            return

        cursor = self.connection.execute("SELECT LATITUDE, LONGITUDE FROM uprn WHERE UPRN = ? LIMIT 1;", [uprn])
        if coords := cursor.fetchone():
            item["lat"], item["lon"] = coords
            item["extras"]["source:geometry"] = "OS Open UPRN"

        cursor = self.connection.execute("SELECT TRIM(postcode) FROM uprn2postcode WHERE uprn = ? LIMIT 1;", [uprn])
        if pc := cursor.fetchone():
            item["postcode"] = pc[0]
            item["extras"]["source:addr:postcode"] = "ONSUD"
