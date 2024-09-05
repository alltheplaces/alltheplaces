import re

import scrapy
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, DELIMITERS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours


class WildberriesSpider(scrapy.Spider):
    name = "wildberries"
    start_urls = ["https://www.wildberries.ru/services/besplatnaya-dostavka?desktop=1"]
    item_attributes = {"brand": "Wildberries", "brand_wikidata": "Q24933714"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 100}

    def parse(self, response):
        js_file = response.xpath('//script[contains(@src, "j/spa/index.min.")]/@src').get()
        yield Request(f"https:{js_file}", callback=self.get_poi_file)

    def get_poi_file(self, response):
        all_pickups_name = re.search(r"allPickupsName=\"(.*?)\"", response.text).group(1)
        yield Request(f"https://static-basket-01.wbbasket.ru/vol0/data/{all_pickups_name}", callback=self.parse_poi)

    def parse_poi(self, response):
        for country in response.json():
            for poi in country["items"]:
                if poi.get("isExternalPostamat"):
                    # Parsel lockers for inhabitants of a specific building,
                    # not available for public.
                    continue
                if poi.get("dtype") == 6:
                    # Around 15 partner pickup points - we are not interested in them
                    continue
                item = DictParser.parse(poi)
                item["country"] = country["country"]
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
