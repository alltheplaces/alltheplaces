from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class LeeAUSpider(StockInStoreSpider):
    name = "lee_au"
    item_attributes = {"brand": "Lee", "brand_wikidata": "Q1632681", "extras": Categories.SHOP_CLOTHES.value}
    api_site_id = "10062"
    api_widget_id = "69"
    api_widget_type = "sis"
    api_origin = "https://leejeans.com.au"
