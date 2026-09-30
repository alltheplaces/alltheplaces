import base64
import json
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SnipesSpider(JSONBlobSpider):
    name = "snipes"
    item_attributes = {"brand": "Snipes", "brand_wikidata": "Q42306166", "name": "Snipes"}
    requires_proxy = True
    locations_key = "shops"
    # Storefront context and its Scayle shop ID, from the CONFIG ng-state of /<context>/storefinder
    SHOPS = {
        "de-at": 1051,
        "fr-be": 1061,
        "de-ch": 1057,
        "de-de": 1048,
        "es-es": 1036,
        "fr-fr": 1042,
        "hr-hr": 1001,
        "it-it": 1039,
        "nl-nl": 1054,
        "pl-pl": 1045,
        "pt-pt": 1033,
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for context, shop_id in self.SHOPS.items():
            # Same URL for every country: the shop is selected by the X-Charybdis header only
            yield JsonRequest(
                url="https://api.snipes.com/sni-pl-prd-stor-we-char/v1/v1/stores/",
                headers={"X-Charybdis": base64.b64encode(json.dumps({"scayleShopId": shop_id}).encode()).decode()},
                meta={"context": context},
                dont_filter=True,
            )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        ref = feature.get("referenceKey")
        if not ref or not feature.get("isActive"):
            return
        item["ref"] = ref
        if name := item.pop("name", None):
            # "2.0" is the store concept generation, not part of the location name
            item["branch"] = name.removesuffix(f" - {ref}").removesuffix(" 2.0")
        item["phone"] = (feature.get("customData") or {}).get("storePhoneNumber")
        if slug := feature.get("slug"):
            item["website"] = f"https://www.snipes.com/{response.meta['context']}/storefinder/{slug}"

        opening_times = feature.get("openingTimes") or {}
        if any(opening_times.get(day.lower()) for day in DAYS_3_LETTERS):
            item["opening_hours"] = OpeningHours()
            for day in DAYS_3_LETTERS:
                ranges = opening_times.get(day.lower())
                if ranges == []:
                    item["opening_hours"].set_closed(day)
                for time_range in ranges or []:
                    item["opening_hours"].add_range(day, time_range.get("timeFrom"), time_range.get("timeUntil"))

        apply_category(Categories.SHOP_SHOES, item)
        yield item
