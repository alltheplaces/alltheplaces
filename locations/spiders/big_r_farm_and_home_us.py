import re
from typing import Iterable

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class BigRFarmAndHomeUSSpider(AmastyStoreLocatorSpider):
    """
    Big R Farm & Home is a small family-owned farm/ranch/home supply chain
    based in Olney, IL, previously known as Rural King Supply (not to be
    confused with the much larger, unrelated "Rural King" chain covered by
    rural_king_us.py). The address fields are only available as plain text
    within the "popup_html" blob returned by the Amasty store locator, so
    they are extracted here with a regex rather than relying on separate
    JSON fields.
    """

    name = "big_r_farm_and_home_us"
    item_attributes = {"brand": "Big R Farm and Home", "name": "Big R Farm & Home"}
    allowed_domains = ["www.bigrfarmandhome.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector | None = None) -> Iterable[Feature]:
        popup_text = feature.get("popup_html") or ""
        for field, key in [("City", "city"), ("Zip", "postcode"), ("Address", "street_address"), ("State", "state")]:
            if m := re.search(rf"{field}:\s*(.*?)\s*<br>", popup_text):
                item[key] = m.group(1)

        # A minority of records duplicate "City, ST Zip" onto the end of the
        # street address, so strip that back off when present.
        if item.get("street_address") and item.get("city") and item.get("postcode"):
            item["street_address"] = re.sub(
                rf",?\s*{re.escape(item['city'])},?\s*[A-Z]{{2}}\s*{re.escape(item['postcode'])}\s*$",
                "",
                item["street_address"],
            ).strip()

        # The source "name" is just a "City, ST" map pin label, not a store name.
        item["branch"] = item.pop("name")

        apply_category(Categories.SHOP_AGRARIAN, item)

        yield item
