import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ThieleDKSpider(scrapy.Spider):
    name = "thiele_dk"
    item_attributes = {"brand": "Thiele", "brand_wikidata": "Q12339176"}
    start_urls = [
        "https://www.thiele.dk/index.php/tools/search?lat=56.26392&lng=9.501785&radius=10000&units=kilometers",
    ]

    def parse(self, response, **kwargs):
        for store in response.json():
            item = DictParser.parse(store)
            item["email"] = None
            apply_category(Categories.SHOP_OPTICIAN, item)
            yield item
