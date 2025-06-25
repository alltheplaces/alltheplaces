from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class TheBodyShopCASpider(StockistSpider):
    name = "the_body_shop_ca"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}
    key = "map_r325r4wq"

    def parse_item(self, item: Feature, location: dict):
        item["branch"] = item.pop("name")
        yield item
