from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CooplandsGBSpider(WPStoreLocatorSpider):
    name = "cooplands_gb"
    item_attributes = {"brand": "Cooplands", "brand_wikidata": "Q5167971", "extras": Categories.SHOP_BAKERY.value}
    allowed_domains = ["cooplands-bakery.co.uk"]
    iseadgg_countries_list = ["GB"]
    search_radius = 24
    max_results = 50
    days = DAYS_EN
