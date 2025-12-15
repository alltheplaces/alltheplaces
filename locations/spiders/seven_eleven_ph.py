from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.geo import city_locations
from locations.hours import DAYS_EN
from locations.items import set_closed
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SevenElevenPHSpider(WPStoreLocatorSpider):
    name = "seven_eleven_ph"
    allowed_domains = ["www.7-eleven.com.ph"]
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    days = DAYS_EN

    async def start(self):
        for city in city_locations("PH"):
            lat = city.get("latitude")
            lon = city.get("longitude")
            yield JsonRequest(
                f"https://www.7-eleven.com.ph/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results=100&search_radius=500&filter=62",
            )

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        if "[PERMANENT CLOSED]" in item["street_address"]:
            set_closed(item)
        self.clean_address(item)
        if item.get("phone") == "20000000":
            # Drop a test/fake phone number
            item["phone"] = None
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item

    def clean_address(self, item):
        for term in ["[OPEN]", "[TEMPORARY CLOSED]", "[PERMANENT CLOSED]"]:
            if term in item["street_address"]:
                item["street_address"] = item["street_address"].replace(term, "").strip()
                break
