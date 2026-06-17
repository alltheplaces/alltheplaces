import csv
from io import BytesIO, TextIOWrapper
from typing import Any, AsyncIterator, Self
from zipfile import ZipFile

from scrapy import Request
from scrapy.crawler import Crawler
from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature


class OwenBaseSpider(AddressSpider):
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 60 * 5}
    no_refs = True

    drive_id: str
    csv_filename: str

    postal_towns = {}

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        with open("locations/spiders/addresses/gb/postal_cities.csv") as f:
            for r in csv.DictReader(f):
                spider.postal_towns[r["Outward Code"]] = r["addr:city"]
        return spider

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            "https://drive.usercontent.google.com/download?id={}&export=download&confirm=t".format(self.drive_id)
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        with ZipFile(BytesIO(response.body)) as zip_file:
            for addr in csv.DictReader(TextIOWrapper(zip_file.open(self.csv_filename), encoding="utf-8")):
                item = Feature()
                item["ref"] = addr.get("PROPREF")
                item["extras"]["ref:GB:uprn"] = addr.get("UPRN")
                item["lat"] = addr["LAT"]
                item["lon"] = addr["LNG"]
                item["postcode"] = addr["POSTCODE"]
                item["country"] = "GB"

                self.parse_row(item, addr)

                if not item.get("city") and item.get("postcode"):
                    item["city"] = self.postal_towns.get(item["postcode"].split(" ", 1)[0])

                yield item

    def parse_row(self, item: Feature, addr: dict):
        raise NotImplementedError
