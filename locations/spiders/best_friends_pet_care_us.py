import html
import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

# The locator runs the WP Store Locator plugin and covers the whole Best
# Friends Pet Care network: the brand's own hotels plus the independently named
# pet care businesses it partners with, each with its own site.
#
# The brand is therefore set per record rather than for the whole spider, and
# the partner businesses keep their own name.
#
# One record has its city and state the wrong way round, which is corrected.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class BestFriendsPetCareUSSpider(WPStoreLocatorSpider):
    name = "best_friends_pet_care_us"
    allowed_domains = ["www.bestfriendspetcare.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        store = html.unescape(location.get("store") or "").strip()

        if "best friends pet" in store.lower():
            item["brand"] = "Best Friends Pet Hotel"
            item["name"] = None
            item["branch"] = location.get("city")
        else:
            item["name"] = store

        item["website"] = location.get("permalink")

        # One record carries "Denver" as its state and "CO" as its city.
        if not re.fullmatch(r"[A-Z]{2}", item.get("state") or "") and re.fullmatch(
            r"[A-Z]{2}", item.get("city") or ""
        ):
            item["city"], item["state"] = item["state"], item["city"]

        apply_category(Categories.ANIMAL_BOARDING, item)

        yield item
