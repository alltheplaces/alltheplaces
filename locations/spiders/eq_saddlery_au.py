from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class EqSaddleryAUSpider(StockInStoreSpider):
    name = "eq_saddlery_au"
    item_attributes = {"brand": "EQ Saddlery", "brand_wikidata": "Q117746041", "extras": Categories.SHOP_SPORTS.value}
    api_site_id = "10040"
    api_widget_id = "47"
    api_widget_type = "sis"
    api_origin = "https://www.eqsaddlery.com.au"
