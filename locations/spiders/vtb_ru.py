import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# TODO: scrape ATMs from
# https://online.vtb.ru/msa/api-gw/attm/attm-dictionary/atm/nearby/filtered/?longitude=36.6153309807117&latitude=54.66560792903764&radius=100


DAYS_MAPPING = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su",
}


class VtbRUSpider(scrapy.Spider):
    name = "vtb_ru"
    allowed_domains = ["vtb.ru"]
    start_urls = ["https://headless-cms3.vtb.ru/projects/atm/models/default/items/departments"]
    item_attributes = {"brand": "ВТБ", "brand_wikidata": "Q1549389"}

    def parse(self, response):
        for poi in response.json()["branches"]:
            poi.update(poi.pop("coordinates"))
            item = DictParser.parse(poi)
            item["ref"] = poi["Biskvit_id"]
            apply_category(Categories.BANK, item)
            self.parse_hours(item, poi)
            yield item

    def parse_hours(self, item, poi):
        if hours := poi.get("scheduleFl"):
            try:
                oh = OpeningHours()
                for day_number, times in hours.items():
                    # Days off
                    if times == "выходной":
                        continue
                    day = DAYS_MAPPING.get(day_number)
                    open, close = times.split("-")
                    oh.add_range(day, open, close)

                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Couldn't parse hours: {hours}, {e}")
