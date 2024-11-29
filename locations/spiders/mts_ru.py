import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, DELIMITERS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours


class MtsRUSpider(scrapy.Spider):
    name = "mts_ru"
    item_attributes = {"brand_wikidata": "Q1368919"}
    start_urls = ["https://moskva.mts.ru/api/bff/v1/offices/points"]

    def parse(self, response):
        for poi in response.json():
            item = DictParser.parse(poi)
            # Coords are switched in raw data
            item["lat"] = poi["longitude"]
            item["lon"] = poi["latitude"]
            self.parse_hours(item, poi)
            apply_category(Categories.SHOP_TELECOMMUNICATION, item)
            yield item

    def parse_hours(self, item, poi):
        if details := poi.get("details", []):
            details = [d for d in details if d]
            if len(details) == 0:
                return
            try:
                oh = OpeningHours()
                oh.add_ranges_from_string(details[0], DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, DELIMITERS_RU)
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours: {details}, {item['ref']}, {e}")
