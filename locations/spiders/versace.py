import re
from typing import Iterable

from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class VersaceSpider(JSONBlobSpider):
    name = "versace"
    item_attributes = {"brand": "Versace", "brand_wikidata": "Q696376"}
    allowed_domains = ["www.versace.com"]
    start_urls = ["https://www.versace.com/on/demandware.store/Sites-US-Site/en_US/Stores-Search"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def extract_json(self, response: TextResponse) -> list[dict]:
        return response.json()["stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = (
            re.compile(r"^(?:(?:young versace|versace jeans couture|versace outlet|versace)\b\s*)+", re.IGNORECASE)
            .sub("", item.pop("name", ""))
            .strip()
        )
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(feature.get("storeHours"))
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
