import chompjs
import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class RottenRobbieUSSpider(scrapy.Spider):
    name = "rotten_robbie_us"
    item_attributes = {"brand": "Rotten Robbie", "brand_wikidata": "Q87378070"}
    start_urls = ["https://rottenrobbie.com/locations"]

    def parse(self, response: Response, **kwargs):
        for store in chompjs.parse_js_object(response.xpath('//*[@type="application/ld+json"]/text()').get())["@graph"]:
            item = DictParser.parse(store)
            item["ref"] = store["@id"]
            item["branch"] = item.pop("name")
            apply_category(Categories.FUEL_STATION, item)
            yield item
