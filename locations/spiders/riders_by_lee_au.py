from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class RidersByLeeAUSpider(StockInStoreSpider):
    name = "riders_by_lee_au"
    item_attributes = {
        "brand": "Riders by Lee",
        "brand_wikidata": "Q117747538",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    api_site_id = "10057"
    api_widget_id = "64"
    api_widget_type = "sis"
    api_origin = "https://ridersbylee.com.au"
