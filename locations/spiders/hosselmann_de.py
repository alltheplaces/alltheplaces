from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HosselmannDESpider(WPStoreLocatorSpider):
    name = "hosselmann_de"
    item_attributes = {"brand_wikidata": "Q107203160", "brand": "Hosselmann", "extras": Categories.SHOP_BAKERY.value}
    allowed_domains = [
        "hosselmann.de",
    ]
    iseadgg_countries_list = ["DE"]
    search_radius = 24
    max_results = 50
    days = DAYS_EN
