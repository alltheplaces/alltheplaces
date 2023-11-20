import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, OpeningHours

# TODO: scrape ATMs from
# https://online.vtb.ru/msa/api-gw/attm/attm-dictionary/atm/nearby/filtered/?longitude=36.6153309807117&latitude=54.66560792903764&radius=100


class VtbRUSpider(scrapy.Spider):
    name = "vtb_ru"
    allowed_domains = ["vtb.ru"]
    start_urls = ["https://headless-cms3.vtb.ru/projects/atm/models/default/items/departments"]
    item_attributes = {"brand": "ВТБ", "brand_wikidata": "Q1549389"}

    def parse(self, response):
        for poi in response.json()["branches"]:
            poi.update(poi.pop("coordinates"))
            item = DictParser.parse(poi)
            oh = OpeningHours()
            oh.add_ranges_from_string(poi.get("scheduleFl"), DAYS_RU)
            item["opening_hours"] = oh.as_opening_hours()
            apply_category(Categories.BANK, item)
            yield item
