from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SuzukiCASpider(AgileStoreLocatorSpider):
    name = "suzuki_ca"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642", "extras": Categories.SHOP_CAR.value}
    allowed_domains = ["www.suzuki.ca"]
