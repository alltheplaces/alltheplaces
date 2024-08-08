from locations.categories import Categories, apply_category
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CareoneUSSpider(WPStoreLocatorSpider):
    name = "careone_us"
    item_attributes = {"brand": "CareOne", "brand_wikidata": "Q25108589"}
    allowed_domains = ["www.care-one.com"]
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        item.pop("addr_full", None)
        if "Assisted Living" in item.get("name"):
            apply_category({"amenity": "social_facility", "social_facility": "assisted_living"}, item)
        else:
            apply_category(Categories.NURSING_HOME, item)
        yield item
