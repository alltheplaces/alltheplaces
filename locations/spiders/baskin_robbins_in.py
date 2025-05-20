from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class BaskinRobbinsINSpider(StockistSpider):
    name = "baskin_robbins_in"
    item_attributes = {"brand": "Baskin-Robbins", "brand_wikidata": "Q584601"}
    key = "u11410"

    def parse_item(self, item: Feature, location: dict):
        item.pop("email")
        item.pop("website")
        item["addr_full"] = item.pop("street_address", None)

        if item["country"] == "No":
            item["country"] = "IN"
            item["postcode"] = item["state"]
            item["state"] = item["city"]
            item["city"] = location["address_line_2"]

        yield item
