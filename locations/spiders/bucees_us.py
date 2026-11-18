import json

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BuceesUSSpider(Spider):
    name = "bucees_us"
    item_attributes = {"brand": "Buc-ee's", "brand_wikidata": "Q4982335"}
    start_urls = ["https://buc-ees.com/locations/"]

    def parse(self, response: TextResponse, **kwargs):
        for data in json.loads(response.xpath('(//*[@type="application/ld+json"]/text())[2]').get()).get("department"):
            item = DictParser.parse(data)
            item["ref"] = item.pop("name").removeprefix("#").split(" ", 1)[0]
            apply_category(Categories.FUEL_STATION, item)

            yield item
