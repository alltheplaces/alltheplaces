from locations.categories import Categories
from locations.storefinders.storeify import StoreifySpider


class IsportMOSpider(StoreifySpider):
    name = "isport_mo"
    item_attributes = {
        "brand": "iSport",
        # "brand_wikidata": "TBA",
        "extras": Categories.SHOP_SPORTS.value,
    }
    api_key = "isportmo.myshopify.com"
