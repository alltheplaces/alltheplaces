from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.freshop import FreshopSpider


class SendiksUSSpider(FreshopSpider):
    name = "sendiks_us"
    item_attributes = {"brand": "Sendik's Food Market", "brand_wikidata": "Q23461945"}
    app_key = "sendiks"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        if hours_md := location.get("hours_md"):
            if hours_md.endswith("Daily"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string("Daily " + hours_md.removesuffix("Daily"))
        if item["name"].endswith("Fresh2GO"):
            item["branch"] = item["name"].removesuffix(" Fresh2GO")
            item["name"] = "Sendik's Fresh2GO"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            item["branch"] = item["name"]
            item["name"] = "Sendik's"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
