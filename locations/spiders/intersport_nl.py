from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class IntersportNLSpider(StockistSpider):
    name = "intersport_nl"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    key = "u25150"

    def parse_item(self, item: Feature, location: dict):
        item["website"] = location["custom_fields"][0]["value"]
        yield item
