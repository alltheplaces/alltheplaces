import json
from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TheWarehouseGroupNZSpider(JSONBlobSpider):
    name = "the_warehouse_group_nz"
    BRANDS = {
        "thewarehouse": ("The Warehouse", "Q110205200", "twl", Categories.SHOP_DEPARTMENT_STORE),
        "noelleeming": ("Noel Leeming", "Q110205329", "nlg", Categories.SHOP_ELECTRONICS),
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = ["stores", "stores"]

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        for brand in self.BRANDS:
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
                    "https://www.{}.co.nz/on/demandware.store/Sites-{}-Site/default/Stores-FindStores?region={}".format(
                        brand, self.BRANDS[brand][2], region
                    )
                )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["addr_full"] = item["addr_full"].removeprefix("The Warehouse").removeprefix("Noel Leeming")
        item["street_address"] = feature["address1"]

        try:
            item["opening_hours"] = self.parse_opening_hours(json.loads(feature["storeHoursJson"])["openingHours"])
        except:
            self.logger.error("Error parsing opening hours: {}".format(feature["storeHoursJson"]))

        brand = response.url.split(".")[1]
        if brand_details := self.BRANDS.get(brand):
            item["brand"], item["brand_wikidata"] = brand_details[0], brand_details[1]
            apply_category(brand_details[3], item)

        yield item

    def parse_opening_hours(self, rules: list[str]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day, times = rule.split(" ")
            if times == "CLOSED":
                oh.set_closed(day)
            else:
                oh.add_range(day, *times.split("-"))
        return oh
