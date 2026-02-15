from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider
from locations.storefinders.uberall import UberallSpider


class FlyingTigerCopenhagenSpider(UberallSpider):
    name = "flying_tiger_copenhagen"
    item_attributes = {
        "brand": "Flying Tiger Copenhagen",
        "brand_wikidata": "Q2786319",
    }
    key = "NDob50utCroANd8wbRBCFBYHC27U0T"

    async def start(self) -> AsyncIterator[JsonRequest]:
        async for request in super().start():
            yield request
        yield JsonRequest(
            url="https://stockist.co/api/v1/u7767/locations/all",
            callback=self.parse_stockist,
        )

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        # Name is always the brand name, not a branch name
        item.pop("name", None)
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item

    def parse_stockist(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json():
            item = StockistSpider.parse_location(location)
            # Name is the address, not a branch name
            item.pop("name", None)
            oh = OpeningHours()
            for field in location.get("custom_fields", []):
                if field["name"] == "Store Number":
                    item["ref"] = field["value"]
                elif field["name"] in DAYS_FULL:
                    if field.get("value"):
                        oh.add_ranges_from_string(f"{field['name']} {field['value']}")
            item["opening_hours"] = oh
            apply_category(Categories.SHOP_VARIETY_STORE, item)
            yield item
