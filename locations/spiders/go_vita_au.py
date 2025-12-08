from locations.categories import Categories
from locations.storefinders.stockist import StockistSpider


class GoVitaAUSpider(StockistSpider):
    name = "go_vita_au"
    item_attributes = {"brand": "Go Vita", "brand_wikidata": "Q126165276", "extras": Categories.SHOP_HEALTH_FOOD.value}
    key = "u8710"

    def parse_item(self, item, location):
        yield item
