from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class OxfordAUSpider(StockInStoreSpider):
    name = "oxford_au"
    item_attributes = {"brand": "Oxford", "brand_wikidata": "Q117747475", "extras": Categories.SHOP_CLOTHES.value}
    api_site_id = "10078"
    api_widget_id = "85"
    api_widget_type = "cnc"
    api_origin = "https://www.oxfordshop.com.au"
