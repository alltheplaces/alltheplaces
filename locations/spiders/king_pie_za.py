import re
from typing import Iterable

from parsel import Selector

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class KingPieZASpider(SuperStoreFinderSpider):
    name = "king_pie_za"
    item_attributes = {"brand": "King Pie", "brand_wikidata": "Q116619039"}
    allowed_domains = ["kingpie.co.za"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item: Feature, location: Selector) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)

        if hours := location.xpath("./operatingHours/text()").get():
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                re.sub(r"<[^>]*>|&nbsp;", " ", hours).replace("24hrs", "00:00 - 23:59")
            )

        apply_category(Categories.FAST_FOOD, item)
        yield item
