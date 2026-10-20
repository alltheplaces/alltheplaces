from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class EkomITSpider(scrapy.Spider):
    name = "ekom_it"
    item_attributes = {"brand": "Ekom", "brand_wikidata": "Q62073442"}
    start_urls = ["https://www.ekomdiscount.it/ebsn/api/warehouse-locator/search"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["warehouses"]:
            item = DictParser.parse(location)
            item["ref"] = location["warehouseId"]
            item["branch"] = item.pop("name").removeprefix("Ekom ")
            item["lat"] = location["address"].get("latitude")
            item["lon"] = location["address"].get("longitude")
            item["housenumber"] = location["address"].get("addressNumber")
            if location.get("metaData"):
                item["phone"] = location["metaData"].get("warehouse_locator", {}).get("PHONE")

            item["opening_hours"] = self.parse_opening_hours(location["serviceHours"])

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item

    def parse_opening_hours(self, service_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for rule in service_hours["default"]:
            day = DAYS[rule["beginWeekDay"] - 2]
            begin_hour = rule["beginHour"]
            end_hour = rule["endHour"]
            if "-" in begin_hour and "-" in end_hour:
                # A minority of records cram a split morning/afternoon opening into a
                # single rule (e.g. beginHour="08:30-13:00", endHour="15:30-19:30")
                # instead of two separate rules like most other records use.
                oh.add_range(day, *begin_hour.split("-"))
                oh.add_range(day, *end_hour.split("-"))
            else:
                oh.add_range(day, begin_hour, end_hour)
        return oh
