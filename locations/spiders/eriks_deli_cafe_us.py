from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider
from locations.hours import DAYS_EN

class EriksDeliCafeUSSpider(WPStoreLocatorSpider):
    name = "eriks_deli_cafe_us"
    item_attributes = {
        "brand_wikidata": "Q116922917",
        "brand": "Erik's DeliCafé",
        "extras": Categories.FAST_FOOD.value
    }
    allowed_domains = [
        "eriksdelicafe.com",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    time_format = "%I:%M %p"
    days = DAYS_EN
