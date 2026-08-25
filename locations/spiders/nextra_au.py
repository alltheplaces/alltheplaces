from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

BRANDS = {
    "nextra": {"brand": "nextra", "brand_wikidata": "Q126174838"},
    "news extra": {"brand": "news extra", "brand_wikidata": "Q126174864"},
}

STATE_NAMES = {
    "New South Wales": "NSW",
    "Victoria": "VIC",
    "Queensland": "QLD",
    "Western Australia": "WA",
    "South Australia": "SA",
    "Tasmania": "TAS",
    "Australian Capital Territory": "ACT",
    "Northern Territory": "NT",
}


class NextraAUSpider(WPStoreLocatorSpider):
    name = "nextra_au"
    allowed_domains = ["nextra.com.au"]
    iseadgg_countries_list = ["AU"]
    search_radius = 100
    max_results = 100
    custom_settings = {"RETRY_HTTP_CODES": [500, 502, 503, 504, 520, 522, 524, 408, 429]}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        branch_name = item.pop("name", None)
        for prefix, brand_attributes in BRANDS.items():
            if branch_name and branch_name.lower().startswith(prefix):
                item.update(brand_attributes)
                item["name"] = brand_attributes["brand"]
                item["branch"] = branch_name[len(prefix) :].strip()
                break
        else:
            self.logger.warning("Could not determine brand for store name '%s'", branch_name)
            item["branch"] = branch_name

        item.pop("addr_full", None)

        if state := item.get("state"):
            item["state"] = STATE_NAMES.get(state, state)

        if website := item.pop("website", None):
            if "facebook.com" in website:
                item["facebook"] = website

        apply_category(Categories.SHOP_NEWSAGENT, item)

        yield item
