from locations.categories import Categories, apply_category
from locations.storefinders.kibo import KiboSpider
from locations.user_agents import BROWSER_DEFAULT


class BiMartUSSpider(KiboSpider):
    name = "bi_mart_us"
    item_attributes = {"brand": "Bi-Mart", "brand_wikidata": "Q4902331"}
    start_urls = ["https://www.bimart.com/api/commerce/storefront/locationUsageTypes/SP/locations"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    api_filter = "tenant~siteId eq 49677 and locationType.Code eq MS"

    def parse_item(self, item, location):
        item.pop("email", None)
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
