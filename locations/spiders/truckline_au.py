from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TrucklineAUSpider(Spider):
    name = "truckline_au"
    item_attributes = {
        "brand": "Truckline",
        "brand_wikidata": "Q126179590",
        "extras": Categories.SHOP_TRUCK_PARTS.value,
    }
    allowed_domains = ["api-v3.partsb2.com.au"]
    start_urls = ["https://api-v3.partsb2.com.au/api/Stores/GetStoresForClient"]

    def start_requests(self) -> Iterable[JsonRequest]:
        headers = {
            "Abp-TenantId": "23",
            "Abp-CustomerId": "cae27e66-79fc-481a-abac-95edf8a652e4",
            "B2v4ApiKey": "truckline.IQhz6BfZZW3794H1Hgf3dKAP8hJfBZZFI2o6654NUv4=",
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, headers=headers)

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in response.json()["result"]:
            item = DictParser.parse(feature)
            item["branch"] = item.pop("name", None)
            item["street_address"] = clean_address([feature.get("address1"), feature.get("address2")])
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(feature.get("openingHours", ""))
            yield item
