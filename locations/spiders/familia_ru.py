import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, DELIMITERS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours


class FamiliaRUSpider(scrapy.Spider):
    name = "familia_ru"
    item_attributes = {"brand": "Familia", "brand_wikidata": "Q127514809"}
    start_urls = ["https://cmssiteprod.famil.ru/api/stores?where%5BisOn%5D%5Bequals%5D=true&limit=0&locale=ru"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for poi in response.json()["docs"]:
            item = DictParser.parse(poi)
            item["state"] = None
            item["city"] = poi["city"]["value"]["city"]
            item["ref"] = poi["storeId"]
            item["extras"]["check_date"] = poi["updatedAt"]
            coordinates = poi.get("coordinatesGroup", {}).get("coordinates", [])
            if len(coordinates) == 2:
                item["lon"], item["lat"] = coordinates
            try:
                if schedule := poi.get("schedule"):
                    oh = OpeningHours()
                    oh.add_ranges_from_string(
                        schedule.replace(".", ""), DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, DELIMITERS_RU
                    )
                    item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours: {schedule}, {item['ref']}, {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
