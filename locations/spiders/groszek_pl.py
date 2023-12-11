from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class GroszekPLSpider(Spider):
    name = "groszek_pl"
    item_attributes = {"brand": "Groszek", "brand_wikidata": "Q9280965"}
    start_urls = ["https://groszek.com.pl/wp-content/themes/groszek/api/js/gps.json"]

    def parse(self, response, **kwargs):
        for feature in response.json()["shops"]:
            item = DictParser.parse(feature)
            item["ref"] = feature["idCRM"]
            item["housenumber"] = feature["number"]
            if feature["format"] == "Supermarket":
                apply_category(Categories.SHOP_SUPERMARKET, item)
            if feature["format"] in ["Market", "Minimarket"]:
                apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
