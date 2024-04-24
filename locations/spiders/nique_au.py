from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class NiqueAUSpider(StockInStoreSpider):
    name = "nique_au"
    item_attributes = {"brand": "Nique", "brand_wikidata": "Q117747324", "extras": Categories.SHOP_CLOTHES.value}
    api_site_id = "10011"
    api_widget_id = "19"
    api_widget_type = "sis"
    api_origin = "https://www.nique.com.au"
