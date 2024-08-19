from html import unescape
from urllib.parse import urljoin

from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BuffaloExchangeUSSpider(WPStoreLocatorSpider):
    name = "buffalo_exchange_us"
    item_attributes = {
        "brand_wikidata": "Q4985721",
        "brand": "Buffalo Exchange",
    }
    allowed_domains = [
        "buffaloexchange.com",
    ]
    days = DAYS_EN
    time_format = "%I:%M %p"
    iseadgg_countries_list = ["US"]
    search_radius = 1000
    max_results = 100

    def parse_item(self, item, location):
        if "PERMANENTLY CLOSED" in item["name"]:
            return
        if branch_name := item.pop("name", None):
            item["branch"] = (
                unescape(branch_name).removeprefix("Buffalo Outlet – ").removeprefix("Buffalo Trading Post – ")
            )
        item["website"] = urljoin("https://buffaloexchange.com", item["website"])
        yield item
