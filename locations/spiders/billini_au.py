from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class BilliniAUSpider(StockistSpider):
    name = "billini_au"
    item_attributes = {"brand": "Billini", "brand_wikidata": "Q117747826"}
    key = "u5133"

    def parse_item(self, item: Feature, location: dict):
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
