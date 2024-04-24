from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class NeverlandAUSpider(StockInStoreSpider):
    name = "neverland_au"
    item_attributes = {"brand": "Neverland", "brand_wikidata": "Q117747218", "extras": Categories.SHOP_CLOTHES.value}
    api_site_id = "10095"
    api_widget_id = "102"
    api_widget_type = "storelocator"
    api_origin = "https://neverlandstore.com.au"
