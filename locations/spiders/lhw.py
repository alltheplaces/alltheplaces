from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class LhwSpider(JSONBlobSpider):
    name = "lhw"
    allowed_domains = ["www.lhw.com"]
    start_urls = ["https://www.lhw.com/services/json/FindAllHotelsV2_en.js"]
    item_attributes = {"brand": "The Leading Hotels of the World", "brand_wikidata": "Q834396"}
    locations_key = ["d", "Hotels"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("street_address", None)
        item["addr_full"] = merge_address_lines([feature.get("Address1"), feature.get("Address2")])
        item["ref"] = feature["BookingNumber"]
        item["website"] = feature["Link"]
        apply_category(Categories.HOTEL, item)
        apply_yes_no(Extras.SWIMMING_POOL, item, "Swimming Pool(s)" in feature["Features"])
        apply_yes_no(Extras.PETS_ALLOWED, item, "Pet Friendly - Conditions Apply" in feature["Features"])
        yield item
