from locations.categories import Categories
from locations.hours import DAYS_NL
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CurvesNLSpider(WPStoreLocatorSpider):
    name = "curves_nl"
    item_attributes = {"brand": "Curves International", "brand_wikidata": "Q5196080", "extras": Categories.GYM.value}
    allowed_domains = ["curves.nl"]
    days = DAYS_NL
