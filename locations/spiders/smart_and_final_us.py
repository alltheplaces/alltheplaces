from locations.categories import Categories
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class SmartAndFinalUSSpider(StorefrontgatewaySpider):
    name = "smart_and_final_us"
    item_attributes = {
        "brand": "Smart & Final",
        "brand_wikidata": "Q7543916",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://storefrontgateway.smartandfinal.com/api/stores"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").removeprefix(f"{location['retailerStoreId']} - ")
        item["website"] = f"https://www.smartandfinal.com/sm/planning/rsid/{item['ref']}"
        yield item
