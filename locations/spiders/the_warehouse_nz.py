import json
from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TheWarehouseNZSpider(JSONBlobSpider):
    name = "the_warehouse_nz"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = {"brand": "The Warehouse", "brand_wikidata": "Q110205200"}
    locations_key = ["stores", "stores"]

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        for region in [
            "NZ-NTL",
            "NZ-AUK",
            "NZ-WKO",
            "NZ-BOP",
            "NZ-GIS",
            "NZ-TKI",
            "NZ-MWT",
            "NZ-HKB",
            "NZ-WGN",
            "NZ-TAS",
            "NZ-MBH",
            "NZ-WTC",
            "NZ-CAN",
            "NZ-OTA",
            "NZ-STL",
        ]:
            yield Request(
                "https://www.thewarehouse.co.nz/on/demandware.store/Sites-twl-Site/default/Stores-FindStores?region={}".format(
                    region
                )
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        ruleset = json.loads(feature["storeHoursJson"])["openingHours"]
        # item["street_address"] = feature["address1"]
        # item["branch"] = item.pop("name", None)
        item["opening_hours"] = OpeningHours()
        for rules in ruleset:
            item["opening_hours"].add_ranges_from_string(rules)
        yield item
