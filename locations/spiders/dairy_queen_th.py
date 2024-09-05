import scrapy

from locations.dict_parser import DictParser


class DairyQueenTHSpider(scrapy.Spider):
    name = "dairy_queen_th"
    item_attributes = {"brand": "Dairy Queen", "brand_wikidata": "Q1141226"}
    start_urls = [
        "https://www.dairyqueenthailand.com/mapen",
    ]
    no_refs = True

    def parse(self, response, **kwargs):
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = store.get("content")
            yield item
