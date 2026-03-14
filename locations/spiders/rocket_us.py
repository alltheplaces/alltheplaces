from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class RocketUSSpider(Spider):
    name = "rocket_us"
    item_attributes = {"brand": "Rocket", "brand_wikidata": "Q121513516"}
    start_urls = ["https://rocketstores.com/wp-json/stations/v1/locations"]

    def parse(self, response, **kwargs):
        for location in response.json()["stations"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name", None)
            item["street_address"] = location["address"]
            item.pop("addr_full", None)
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
