from locations.categories import Categories
from locations.storefinders.kibo import KiboSpider
from locations.user_agents import BROWSER_DEFAULT


class BiMartUSSpider(KiboSpider):
    name = "bi_mart_us"
    item_attributes = {
        "brand": "Bi-Mart",
        "brand_wikidata": "Q4902331",
        "extras": Categories.SHOP_DEPARTMENT_STORE.value,
    }
    start_urls = ["https://www.bimart.com/api/commerce/storefront/locationUsageTypes/SP/locations"]
    user_agent = BROWSER_DEFAULT
    api_filter = "tenant~siteId eq 49677 and locationType.Code eq MS"

    def parse_item(self, item, location):
        item.pop("email", None)
        yield item
