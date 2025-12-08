from locations.categories import Categories
from locations.hours import OpeningHours
from locations.storefinders.easy_locator import EasyLocatorSpider


class GigisCupcakesUSSpider(EasyLocatorSpider):
    name = "gigis_cupcakes_us"
    item_attributes = {"brand": "Gigi's Cupcakes", "extras": Categories.SHOP_BAKERY.value}
    api_brand_name = "gigiscupcakesusa"

    def parse_item(self, item, location):
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location["properties"]["additional_info"])
        yield item
