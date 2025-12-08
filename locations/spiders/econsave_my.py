from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class EconsaveMYSpider(AgileStoreLocatorSpider):
    item_attributes = {"brand": "Econsave", "brand_wikidata": "Q61776608", "extras": Categories.SHOP_SUPERMARKET.value}
    name = "econsave_my"
    allowed_domains = [
        "econsave.com.my",
    ]
