from chompjs import parse_js_object
from scrapy import Spider

from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingBDSpider(Spider):
    name = "burger_king_bd"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.burgerkingbangladesh.com/assets/custom/js/microsite_map.js"]
    no_refs = True

    def parse(self, response):
        for location in parse_js_object(response.text.split("var branches = ")[1]):
            item = Feature()
            item["branch"] = location[0].replace("Burger King ", "")
            item["lat"] = location[1]
            item["lon"] = location[2]
            yield item
