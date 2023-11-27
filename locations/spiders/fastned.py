from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FastnedSpider(Spider):
    name = "fastned"
    item_attributes = {"brand": "Fastned", "brand_wikidata": "Q19935749"}
    start_urls = ["https://route.fastned.nl/_api/locations"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)

            apply_category(Categories.CHARGING_STATION, item)
            item["extras"]["operator"] = "Fastned"

            # TODO: connector data available in location["connectors"]
            yield item
