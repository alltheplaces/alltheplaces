from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class TheBodyShopAUSpider(StockistSpider):
    name = "the_body_shop_au"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}
    key = "map_g3y2xkzq"

    def parse_item(self, item: Feature, location: dict):
        item["branch"] = item.pop("name").removeprefix("The Body Shop ")
        yield item
