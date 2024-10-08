from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CareoneUSSpider(WPStoreLocatorSpider):
    name = "careone_us"
    item_attributes = {"brand": "CareOne", "brand_wikidata": "Q25108589"}
    allowed_domains = ["www.care-one.com"]
    time_format = "%I:%M %p"

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs) -> Iterable[Feature]:
        item.pop("addr_full", None)
        if "Assisted Living" in item.get("name"):
            apply_category({"amenity": "social_facility", "social_facility": "assisted_living"}, item)
        else:
            apply_category(Categories.NURSING_HOME, item)
        yield item
