import re

from locations.storefinders.woosmap import WoosmapSpider


class HollandAndBarrettSpider(WoosmapSpider):
    name = "holland_and_barrett"
    item_attributes = {"brand": "Holland & Barrett", "brand_wikidata": "Q5880870"}
    key = "woos-7dcebde8-9cf4-37a7-bac3-1dce1c0942ee"
    origin = "https://www.hollandandbarrett.com"

    def parse_item(self, item, feature):
        item["name"] = re.sub(r"\(\d+\)", "", item["name"]).strip()
        item["website"] = "https://www.hollandandbarrett.com" + feature["properties"]["user_properties"]["storePath"]
        yield item
