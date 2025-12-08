from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PetlandUSSpider(WPStoreLocatorSpider):
    name = "petland_us"
    item_attributes = {"brand_wikidata": "Q17111474", "brand": "Petland", "extras": Categories.SHOP_PET.value}
    allowed_domains = [
        "petland.com",
    ]
    days = DAYS_EN
