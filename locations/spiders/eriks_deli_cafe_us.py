from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class EriksDeliCafeUSSpider(WPStoreLocatorSpider):
    name = "eriks_deli_cafe_us"
    item_attributes = {"brand_wikidata": "Q116922917", "brand": "Erik's DeliCafé", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "eriksdelicafe.com",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    days = DAYS_EN
