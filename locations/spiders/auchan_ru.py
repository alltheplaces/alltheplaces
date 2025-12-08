import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature


class AuchanRUSpider(scrapy.Spider):
    name = "auchan_ru"
    start_urls = ["https://www.auchan.ru/v1/shops/external-list"]
    requires_proxy = "RU"

    def parse(self, response):
        for poi in response.json():
            item = DictParser.parse(poi)
            item["state"] = None  # Region values are not accurate
            self.parse_hours(item, poi)
            if item.get("name", "").lower().startswith("атак "):
                item["brand_wikidata"] = "Q2868738"
            else:
                item["brand_wikidata"] = "Q110053013"
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item

    def parse_hours(self, item: Feature, poi: dict):
        if hours := poi.get("opening_hours"):
            try:
                oh = OpeningHours()
                for h in hours:
                    weekdays = DAYS_WEEKDAY if h["weekdays"] == "workdays" else DAYS_WEEKEND
                    open_time = "00:00" if h["is_around_the_clock"] else h["open_time"]
                    close_time = "23:59" if h["is_around_the_clock"] else h["close_time"]
                    oh.add_days_range(weekdays, open_time, close_time, "%H:%M:%S")
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Error parsing hours: {hours}, {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
