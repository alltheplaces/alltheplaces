from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FoodlandUSSpider(AgileStoreLocatorSpider):
    name = "foodland_us"
    item_attributes = {"extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["foodland.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item, location):
        if location["title"].startswith("Foodland Farms "):
            item["brand"] = "Foodland Farms"
            item["brand_wikidata"] = "Q124987342"
        elif location["title"].startswith("Foodland "):
            item["brand"] = "Foodland"
            item["brand_wikidata"] = "Q5465560"
        elif location["title"].startswith("Sack N Save "):
            item["brand"] = "Sack 'N Save"
            item["brand_wikidata"] = "Q124987338"
        yield item
