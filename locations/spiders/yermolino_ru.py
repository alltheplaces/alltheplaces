from typing import Iterable

import w3lib.html
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours
from locations.items import Feature


class YermolinoRUSpider(Spider):
    name = "yermolino_ru"
    allowed_domains = ["www.ermolino-produkty.ru"]
    item_attributes = {"brand_wikidata": "Q109995205"}
    start_urls = ["https://www.ermolino-produkty.ru/magaziny?ac=coords&cat=2"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for poi in response.json()["points"]:
            item = DictParser.parse(poi)
            item["addr_full"] = w3lib.html.remove_tags(item["addr_full"])
            item["lat"] = poi["coords"][0]
            item["lon"] = poi["coords"][1]
            self.parse_hours(item, poi)
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item

    def parse_hours(self, item: Feature, poi: dict):
        if hours := poi.get("vremya_raboty"):
            hours = w3lib.html.remove_tags(hours)
            try:
                hours = hours.replace("Время работы: ", "")
                oh = OpeningHours()
                oh.add_ranges_from_string(
                    hours, days=DAYS_RU, named_day_ranges=NAMED_DAY_RANGES_RU, named_times=NAMED_TIMES_RU
                )
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse hours: {hours}, {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
