from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DaylightDonutsUSSpider(WPStoreLocatorSpider):
    days = DAYS_EN
    name = "daylight_donuts_us"
    item_attributes = {
        "brand_wikidata": "Q48970508",
        "brand": "Daylight Donuts",
    }
    allowed_domains = [
        "daylightdonuts.com",
    ]
    time_format = "%I:%M %p"
