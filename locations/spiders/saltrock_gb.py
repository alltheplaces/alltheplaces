from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class SaltrockGBSpider(StockistSpider):
    name = "saltrock_gb"
    item_attributes = {"brand": "Saltrock", "brand_wikidata": "Q7406195"}
    key = "u24162"

    def parse_item(self, item: Feature, location: dict):
        item["branch"] = item.pop("name")
        yield item
