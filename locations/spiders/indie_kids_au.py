from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class IndieKidsAUSpider(StockInStoreSpider):
    name = "indie_kids_au"
    item_attributes = {
        "brand": "Indie Kids",
        "brand_wikidata": "Q117746093",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    api_site_id = "10103"
    api_widget_id = "110"
    api_widget_type = "product"
    api_origin = "https://www.industriekids.com.au"
