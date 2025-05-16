from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockinstore import StockInStoreSpider


class AquilaAUSpider(StockInStoreSpider):
    name = "aquila_au"
    item_attributes = {"brand": "Aquila", "brand_wikidata": "Q17985574"}
    api_site_id = "10049"
    api_widget_id = "56"
    api_widget_type = "sis"
    api_origin = "https://www.aquila.com.au"

    def parse_item(self, item: Feature, location: dict):
        apply_category(Categories.SHOP_SHOES, item)
        yield item
