import re

from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class ShopriteUSSpider(StorefrontgatewaySpider):
    name = "shoprite_us"
    item_attributes = {"brand": "ShopRite", "brand_wikidata": "Q7501097"}
    start_urls = ["https://storefrontgateway.brands.wakefern.com/api/stores"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"X-Site-Host": "https://www.shoprite.com/"}}

    def post_process_item(self, item, response, location):
        if location["type"] != "Regular" or location["name"] == "Test ShopRite":
            return
        item["website"] = f"https://www.shoprite.com/sm/planning/rsid/{item['ref']}"
        split_name = re.split(r"\s+of\s+", item["name"], flags=re.IGNORECASE)
        if len(split_name) == 2:
            item["name"], item["branch"] = split_name
        yield item
