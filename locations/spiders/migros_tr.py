from typing import Iterable

import scrapy
from scrapy.http import Request, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature

CATEGORY_MAPPING = {
    1: {"brand": "Macrocenter", "brand_wikidata": "Q123194881", "extras": Categories.SHOP_SUPERMARKET.value},
    2: {"brand": "Migros", "brand_wikidata": "Q1754510", "extras": Categories.SHOP_SUPERMARKET.value},
    5: {
        # 5M Migros is just bigger version of Migros, as well as MM and MMM
        "brand": "Migros",
        "brand_wikidata": "Q1754510",
        "extras": Categories.SHOP_SUPERMARKET.value,
    },
    8: {"brand": "Migros Jet", "brand_wikidata": "Q1754510", "extras": Categories.SHOP_CONVENIENCE.value},
    10: {"brand": "Kiosk", "extras": Categories.SHOP_CONVENIENCE.value},
    12: {"brand": "Mion", "extras": Categories.SHOP_CHEMIST.value},
    13: {
        # Migros Toptan aka wholesale
        "brand": "Migros",
        "brand_wikidata": "Q1754510",
        "extras": Categories.SHOP_WHOLESALE.value,
    },
}


class MigrosTRSpider(scrapy.Spider):
    name = "migros_tr"
    item_attributes = {"brand": "Migros", "brand_wikidata": "Q1754510"}

    def start_requests(self) -> Iterable[scrapy.Request]:
        yield Request("https://api.migroskurumsal.com/api/StoreLocation/GetStoresWithDetails", method="POST")

    def parse(self, response: Response) -> Iterable[Feature]:
        for poi in response.json()["data"]:
            item = DictParser.parse(poi)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name", "").replace("MİGROS", "").strip()

            if match := CATEGORY_MAPPING.get(poi.get("brandId")):
                item.update(match)
            else:
                self.crawler.stats.inc_value(f'atp/{self.name}/brand/fail/{poi.get("brandId")}/{poi.get("brand")}')
                continue

            self.parse_hours(item, poi)
            yield item

    def parse_hours(self, item: Feature, poi: dict):
        try:
            oh = OpeningHours()
            for day in DAYS_FULL:
                day_field = day.lower() + "Hours"
                if hours_string := poi.get(day_field):
                    if hours_string == "7/24 - 7/24":
                        oh.add_range(DAYS_EN.get(day), "00:00", "23:59")
                        continue

                    hours_string = hours_string.replace(" ", "")
                    open, close = hours_string.split("-")
                    oh.add_range(DAYS_EN.get(day), open, close)

            item["opening_hours"] = oh
        except Exception as e:
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/fail")
            self.logger.warning(f"Failed to parse hours: {poi}, {e}")
