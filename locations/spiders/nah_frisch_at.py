import json
from typing import AsyncIterator

from scrapy import Request
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class NahFrischATSpider(JSONBlobSpider):
    name = "nah_frisch_at"
    item_attributes = {
        "brand": "Nah & Frisch",
        "brand_wikidata": "Q1963643",
        "name": "Nah & Frisch",
    }
    allowed_domains = ["www.nahundfrisch.at"]
    locations_key = ["merchants", "data"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # A single request with a radius large enough to cover all of Austria
        # from a central point returns the full national dataset in one page.
        yield JsonRequest(
            url="https://www.nahundfrisch.at/api/merchant/searchLatLng",
            data={"lat": 47.5, "lng": 14.0, "perPage": 500, "radius": 1000000, "page": 1},
        )

    def pre_process_data(self, feature: dict):
        # "street" already includes the house number, so route it to
        # street_address rather than letting DictParser put an unsplit
        # value into the street-only field.
        feature["street_address"] = feature.pop("street", None)
        if feature.get("zip") is not None:
            feature["zip"] = str(feature["zip"])

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name", None)
        item["website"] = f"https://www.nahundfrisch.at/kaufmann/{location['slug']}"
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield Request(item["website"], callback=self.parse_store_page, cb_kwargs={"item": item})

    def parse_store_page(self, response, item):
        attrib = response.xpath("//opening-times").attrib
        oh = OpeningHours()
        # "hybrid" entries are additional self-service/unstaffed access hours
        # (e.g. a vending area) on top of the staffed "default" hours; both
        # represent times customers can access the store.
        for key in (":opening-hours", ":hybrid-opening-hours"):
            for rule in json.loads(attrib.get(key) or "[]"):
                day = DAYS[int(rule["day"]) - 1]
                oh.add_range(day, rule["start"][:5], rule["end"][:5])
        item["opening_hours"] = oh

        yield item
