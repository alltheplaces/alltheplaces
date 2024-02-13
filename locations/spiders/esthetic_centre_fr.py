from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider
from locations.categories import Categories


class EstheticCenterFRSpider(AgileStoreLocatorSpider):
    name = "esthetic_center_fr"
    item_attributes = {
        "brand_wikidata": "Q123321775",
        "brand": "Esthetic Center",
        "extras": Categories.SHOP_BEAUTY.value,
    }
    allowed_domains = [
        "www.esthetic-center.com",
    ]
