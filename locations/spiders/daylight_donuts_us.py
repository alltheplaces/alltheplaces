from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DaylightDonutsUSSpider(WPStoreLocatorSpider):
    name = "daylight_donuts_us"
    item_attributes = {"brand_wikidata": "Q48970508", "brand": "Daylight Donuts", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "daylightdonuts.com",
    ]
    iseadgg_countries_list = ["US"]
    search_radius = 25
    max_results = 50
    days = DAYS_EN
    download_delay = 0.2
