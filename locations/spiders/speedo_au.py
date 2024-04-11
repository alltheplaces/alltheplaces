from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class SpeedoAUSpider(StockInStoreSpider):
    name = "speedo_au"
    item_attributes = {"brand": "Speedo", "brand_wikidata": "Q1425519", "extras": Categories.SHOP_CLOTHES.value}
    api_site_id = "10058"
    api_widget_id = "65"
    api_widget_type = "sis"
    api_origin = "https://speedo.com.au"
