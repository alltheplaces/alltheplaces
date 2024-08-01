from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class ManningCartellAUSpider(StockInStoreSpider):
    name = "manning_cartell_au"
    item_attributes = {
        "brand": "Manning Cartell",
        "brand_wikidata": "Q117746697",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    api_site_id = "10045"
    api_widget_id = "52"
    api_widget_type = "sis"
    api_origin = "https://www.manningcartell.com.au"
    custom_settings = {"ROBOTSTXT_OBEY": False}
