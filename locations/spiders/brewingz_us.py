from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BrewingzUSSpider(WPStoreLocatorSpider):
    name = "brewingz_us"
    item_attributes = {"brand": "BreWingZ", "brand_wikidata": "Q123022531", "extras": Categories.RESTAURANT.value}
    allowed_domains = ["www.brewingz.com"]
    days = DAYS_EN
