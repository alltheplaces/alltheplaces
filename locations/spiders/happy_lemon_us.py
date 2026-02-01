from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HappyLemonUSSpider(WPStoreLocatorSpider):
    name = "happy_lemon_us"
    allowed_domains = ["happylemonusa.com"]
    item_attributes = {
        "brand": "Happy Lemon",
        "brand_wikidata": "Q109968422",
    }
    iseadgg_countries_list = ["US"]
    search_radius = 500
    max_results = 100
    days = DAYS_EN

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        yield item
