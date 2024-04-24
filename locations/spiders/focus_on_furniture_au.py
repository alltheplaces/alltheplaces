from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class FocusOnFurnitureAUSpider(StockInStoreSpider):
    name = "focus_on_furniture_au"
    item_attributes = {
        "brand": "Focus on Furniture",
        "brand_wikidata": "Q117746060",
        "extras": Categories.SHOP_FURNITURE.value,
    }
    api_site_id = "10100"
    api_widget_id = "107"
    api_widget_type = "product"
    api_origin = "https://focusonfurniture.com.au"

    def parse_item(self, item, location):
        if item.get("email"):
            item["email"] = item["email"].strip()
        yield item
