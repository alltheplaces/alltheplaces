from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DaylightDonutsUSSpider(WPStoreLocatorSpider):
    name = "daylight_donuts_us"
    item_attributes = {"brand": "Daylight Donuts", "brand_wikidata": "Q48970508"}
    allowed_domains = ["daylightdonuts.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 25
    max_results = 50
    days = DAYS_EN
