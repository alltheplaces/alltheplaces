from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class AftersIceCreamUSSpider(StockistSpider):
    name = "baskin_robbins_in"
    item_attributes = {"brand": "Baskin Robbins", "brand_wikidata": "Q584601"}
    key = "u11410"

    def parse_item(self, item, location):
        item.pop("email")
        item.pop("website")
        yield item
