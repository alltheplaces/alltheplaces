from locations.storefinders.wp_store_locator import WPStoreLocatorSpider
from locations.hours import DAYS_EN
from locations.categories import Categories


class BobablasticUSSpider(WPStoreLocatorSpider):
    name = "bobablastic_us"
    item_attributes = {
        "brand_wikidata": "Q108499280",
        "brand": "Bobablastic",
        "extras": Categories.FAST_FOOD.value
    }
    allowed_domains = [
        "bobablastic.com",
    ]
    time_format = "%I:%M %p"
    iseadgg_countries_list = ["US"]
    search_radius = 100
    max_results = 50
    days = DAYS_EN
