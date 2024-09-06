import re
from typing import Any

import chompjs

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider


class FreshstopZASpider(JSONBlobSpider):
    name = "freshstop_za"
    item_attributes = {"brand": "FreshStop", "brand_wikidata": "Q116620734"}
    start_urls = ["https://freshstop.co.za/store-locator/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(
            re.search(r"bhStoreLocatorLocations = (\[.+?\]);", response.text, re.DOTALL).group(1)
        )

    def pre_process_data(self, location) -> Any:
        location["street_address"] = location.pop("address")
        location["postcode"] = location.pop("postal")

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["facebook"] = location.get("store_contact_info_facebook")
        if location.get("store_contact_info_whatsapp") is not None:
            set_social_media(
                item, SocialMedia.WHATSAPP, "+27 " + location.get("store_contact_info_whatsapp").lstrip("0")
            )
        apply_yes_no(Extras.WIFI, item, "yes" in location.get("amenities_wifi"))
        apply_yes_no(Extras.TOILETS, item, "yes" in location.get("amenities_bathroom"))
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
