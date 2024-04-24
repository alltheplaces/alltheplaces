from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class CarlaZampattiSpider(StockInStoreSpider):
    name = "carla_zampatti"
    item_attributes = {
        "brand": "Carla Zampatti",
        "brand_wikidata": "Q87377342",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    api_site_id = "10131"
    api_widget_id = "139"
    api_widget_type = "storelocator"
    api_origin = "https://www.carlazampatti.com.au"

    def parse_item(self, item, location):
        if "David Jones" in item["name"].title():
            return
        yield item
