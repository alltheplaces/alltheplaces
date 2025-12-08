from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class ZompAUSpider(StockInStoreSpider):
    name = "zomp_au"
    item_attributes = {"brand": "ZOMP", "brand_wikidata": "Q117747772", "extras": Categories.SHOP_SHOES.value}
    api_site_id = "10121"
    api_widget_id = "128"
    api_widget_type = "product"
    api_origin = "https://zomp.com.au"
