from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class NaturasiITSpider(scrapy.Spider):
    name = "naturasi_it"
    item_attributes = {"brand": "NaturaSì", "brand_wikidata": "Q60840755"}
    start_urls = ["https://www.naturasi.it/ebsn/api/warehouse-locator/search"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["warehouses"]:
            item = DictParser.parse(location)
            item["ref"] = location["warehouseId"]
            item["branch"] = item.pop("name").removeprefix("NaturaSì ")
            item["lat"] = location["address"].get("latitude")
            item["lon"] = location["address"].get("longitude")
            item["website"] = urljoin("https://www.naturasi.it/punti-vendita/", location["slug"])
            if location.get("metaData"):
                item["phone"] = location.get("metaData").get("warehouse_locator").get("PHONE")

            item["opening_hours"] = self.parse_opening_hours(location["serviceHours"])

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item

    def parse_opening_hours(self, service_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for rule in service_hours["default"]:
            oh.add_range(DAYS[rule["beginWeekDay"] - 2], rule["beginHour"], rule["endHour"])
        return oh
