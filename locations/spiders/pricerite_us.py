import re

from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class PriceriteUSSpider(StorefrontgatewaySpider):
    name = "pricerite_us"
    item_attributes = {"brand": "Price Rite", "brand_wikidata": "Q7242560"}
    start_urls = ["https://storefrontgateway.brands.wakefern.com/api/stores"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"X-Site-Host": "https://www.priceritemarketplace.com/"}}

    def post_process_item(self, item, response, location):
        if location["type"] != "Regular":
            return
        item["website"] = f"https://www.priceritemarketplace.com/sm/planning/rsid/{item['ref']}"
        split_name = re.split(r"\s+of\s+", item["name"], flags=re.IGNORECASE)
        if len(split_name) == 2:
            item["name"], item["branch"] = split_name
        yield item
