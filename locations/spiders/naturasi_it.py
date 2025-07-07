from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


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
            item["opening_hours"] = OpeningHours()
            for day_time in location["serviceHours"]["default"]:
                day = DAYS_FULL[day_time["beginWeekDay"] - 2]
                open_time = day_time["beginHour"]
                close_time = day_time["endHour"]
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
            yield item
