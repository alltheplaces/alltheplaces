import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, DELIMITERS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours


class WildberriesSpider(scrapy.Spider):
    name = "wildberries"
    allowed_domains = ["www.wildberries.ru"]
    start_urls = ["https://www.wildberries.ru/webapi/spa/modules/pickups"]
    item_attributes = {"brand": "Wildberries", "brand_wikidata": "Q24933714"}

    def parse(self, response):
        for poi in response.json()["value"]["pickups"]:
            if poi.get("isExternalPostamat"):
                # Parsel lockers for inhabitants of a specific building,
                # not available for public.
                continue
            if poi.get("dtype") == 6:
                # Around 15 partner pickup points - we are not interested in them
                continue
            item = DictParser.parse(poi)
            item["lat"] = poi["coordinates"][0]
            item["lon"] = poi["coordinates"][1]
            self.parse_hours(item, poi)
            apply_category(Categories.SHOP_OUTPOST, item)
            yield item

    def parse_hours(self, item, poi):
        if hours := poi.get("workTime"):
            try:
                oh = OpeningHours()
                oh.add_ranges_from_string(hours, DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, DELIMITERS_RU)
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours: {hours}, error: {e}")
