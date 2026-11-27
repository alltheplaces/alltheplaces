from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class OhioCatUSSpider(WPStoreLocatorSpider):
    name = "ohio_cat_us"
    item_attributes = {"brand_wikidata": "Q115486235", "brand": "Ohio CAT", "extras": Categories.SHOP_TRADE.value}
    allowed_domains = [
        "ohiocat.com",
    ]
    start_urls = [
        "https://www.ohiocat.com/wp-admin/admin-ajax.php?action=store_search&lat=39.9625112&lng=-83.0032218&autoload=1"
    ]
    days = DAYS_EN
