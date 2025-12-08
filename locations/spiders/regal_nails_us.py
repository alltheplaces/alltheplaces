from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class RegalNailsUSSpider(WPStoreLocatorSpider):
    name = "regal_nails_us"
    item_attributes = {"brand": "Regal Nails", "brand_wikidata": "Q108918028"}
    allowed_domains = ["regalnails.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 50
    max_results = 100
    days = DAYS_EN
