from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DrKongHKSpider(WPStoreLocatorSpider):
    name = "dr_kong_hk"
    item_attributes = {"brand_wikidata": "Q116547631", "brand": "Dr. Kong", "extras": Categories.SHOP_SHOES.value}
    allowed_domains = [
        "www.dr-kong.com.hk",
    ]
    days = DAYS_EN
