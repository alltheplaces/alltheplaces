import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, DELIMITERS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours


class WildberriesSpider(scrapy.Spider):
    name = "wildberries"
    allowed_domains = ["www.wildberries.ru"]
    start_urls = ["https://static-basket-01.wbbasket.ru/vol0/data/all-poo-fr-v10.json"]
    item_attributes = {"brand": "Wildberries", "brand_wikidata": "Q24933714"}

    def parse(self, response):
        for country in response.json():
            for poi in country["items"]:
                if poi.get("isExternalPostamat"):
                    # Parsel lockers for inhabitants of a specific building,
                    # not available for public.
                    continue
                if poi.get("isHkn"):
                    # For household needs
                    continue
                if poi.get("emp"):
                    # For employees
                    continue
                if poi.get("isSortCenter"):
                    continue
                if poi.get("typePoint") == 14:
                    # Russian Post offices
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
