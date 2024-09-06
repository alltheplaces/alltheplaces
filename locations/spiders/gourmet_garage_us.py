import re

from locations.categories import Categories
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class GourmetGarageUSSpider(StorefrontgatewaySpider):
    name = "gourmet_garage_us"
    item_attributes = {
        "brand": "Gourmet Garage",
        "brand_wikidata": "Q16994340",
        "name": "Gourmet Garage",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://storefrontgateway.brands.wakefern.com/api/stores"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"X-Site-Host": "https://www.gourmetgarage.com/"}}

    def post_process_item(self, item, response, location):
        if location["type"] != "Regular":
            return
        item["website"] = f"https://www.gourmetgarage.com/sm/planning/rsid/{item['ref']}"
        split_name = re.split(r"\s+of\s+", item["name"], flags=re.IGNORECASE)
        if len(split_name) == 2:
            item["name"], item["branch"] = split_name
        yield item
