from locations.items import Feature
from locations.storefinders.metizsoft import MetizsoftSpider


class BosCoffeePHSpider(MetizsoftSpider):
    name = "bos_coffee_ph"
    item_attributes = {
        "brand_wikidata": "Q30591352",
        "brand": "Bo's Coffee",
    }
    shopify_url = "bos-coffee.myshopify.com"

    def parse_item(self, item: Feature, location: dict):
        item.pop("website")
        yield item
