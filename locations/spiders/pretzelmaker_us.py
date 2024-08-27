from locations.storefinders.wp_store_locator import WPStoreLocatorSpider
from locations.hours import DAYS_EN
from locations.categories import Categories


class PretzelmakerUSSpider(WPStoreLocatorSpider):
    name = "pretzelmaker_us"
    item_attributes = {
        "brand_wikidata": "Q7242321",
        "brand": "Pretzelmaker",
        "extras": Categories.FAST_FOOD.value
    }
    allowed_domains = [
        "www.pretzelmaker.com",
    ]
    time_format = "%I:%M %p"
    days = DAYS_EN
