import re

from locations.categories import Categories
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class TheFreshGrocerUSSpider(StorefrontgatewaySpider):
    name = "the_fresh_grocer_us"
    item_attributes = {
        "brand": "The Fresh Grocer",
        "brand_wikidata": "Q18389721",
        "name": "The Fresh Grocer",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://storefrontgateway.brands.wakefern.com/api/stores"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"X-Site-Host": "https://www.thefreshgrocer.com/"}}

    def post_process_item(self, item, response, location):
        if location["type"] != "Regular":
            return
        item["website"] = f"https://www.thefreshgrocer.com/sm/planning/rsid/{item['ref']}"
        split_name = re.split(r"\s+of\s+", item["name"], flags=re.IGNORECASE)
        if len(split_name) == 2:
            item["name"], item["branch"] = split_name
        yield item
