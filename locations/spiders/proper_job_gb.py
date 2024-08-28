from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ProperJobGBSpider(WPStoreLocatorSpider):
    name = "proper_job_gb"
    item_attributes = {"brand_wikidata": "Q83741810", "brand": "Proper Job", "extras": Categories.SHOP_HARDWARE.value}
    allowed_domains = [
        "www.properjob.biz",
    ]
    days = DAYS_EN
