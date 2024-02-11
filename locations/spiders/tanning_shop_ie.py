from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TanningShopIESpider(AgileStoreLocatorSpider):
    name = "tanning_shop_ie"
    item_attributes = {"brand_wikidata": "Q123101132", "brand": "Tanning Shop", "extras": Categories.SHOP_BEAUTY.value}
    allowed_domains = [
        "thetanningshop.co.uk",
    ]
