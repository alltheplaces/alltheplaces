from locations.categories import Categories, apply_category
from locations.storefinders.stockinstore import StockInStoreSpider


class RolerAUSpider(StockInStoreSpider):
    name = "roler_au"
    item_attributes = {"brand": "Roler", "brand_wikidata": "Q117747576"}
    api_site_id = "10101"
    api_widget_id = "108"
    api_widget_type = "product"
    api_origin = "https://roler.com.au"

    def parse_item(self, item, location):
        if "INDUSTRIE" in item["name"].upper():
            return
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
