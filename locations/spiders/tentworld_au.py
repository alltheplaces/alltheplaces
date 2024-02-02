from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class TentworldAUSpider(StockInStoreSpider):
    name = "tentworld_au"
    item_attributes = {"brand": "Tentworld", "brand_wikidata": "Q117747711", "extras": Categories.SHOP_OUTDOOR.value}
    api_site_id = "30"
    api_widget_id = "7"
    api_widget_type = "sis"
    api_origin = "https://www.tentworld.com.au"
