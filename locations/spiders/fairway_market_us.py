import re

from locations.categories import Categories
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class FairwayMarketUSSpider(StorefrontgatewaySpider):
    name = "fairway_market_us"
    item_attributes = {
        "brand": "Fairway Market",
        "brand_wikidata": "Q5430910",
        "name": "Fairway Market",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://storefrontgateway.brands.wakefern.com/api/stores"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"X-Site-Host": "https://www.fairwaymarket.com/"}}

    def post_process_item(self, item, response, location):
        if location["type"] != "Regular":
            return
        item["website"] = f"https://www.fairwaymarket.com/sm/planning/rsid/{item['ref']}"
        split_name = re.split(r"\s+of\s+", item["name"], flags=re.IGNORECASE)
        if len(split_name) == 2:
            item["name"], item["branch"] = split_name
        yield item
