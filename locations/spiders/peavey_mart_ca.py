from locations.categories import Categories
from locations.storefinders.kibo import KiboSpider
from locations.user_agents import BROWSER_DEFAULT


class PeaveyMartCASpider(KiboSpider):
    name = "peavey_mart_ca"
    item_attributes = {
        "brand": "Peavey Mart",
        "brand_wikidata": "Q7158483",
        "extras": Categories.SHOP_COUNTRY_STORE.value,
    }
    start_urls = ["https://www.peaveymart.com/api/commerce/storefront/locationUsageTypes/SP/locations"]
    user_agent = BROWSER_DEFAULT

    def parse_item(self, item, location):
        location_types = [location_type["code"] for location_type in location["locationTypes"]]
        if "STORE" not in location_types:
            return
        item["website"] = "https://www.peaveymart.com/store-details?locationCode=" + item["ref"]
        yield item
