from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class WranglerAUSpider(StockInStoreSpider):
    name = "wrangler_au"
    item_attributes = {"brand": "Wrangler", "brand_wikidata": "Q1445358", "extras": Categories.SHOP_CLOTHES.value}
    api_site_id = "10061"
    api_widget_id = "68"
    api_widget_type = "sis"
    api_origin = "https://wrangler.com.au"
