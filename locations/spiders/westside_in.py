import re
from typing import AsyncIterator, Iterable
from urllib.parse import quote

from scrapy.http import JsonRequest, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WestsideINSpider(JSONBlobSpider):
    name = "westside_in"
    item_attributes = {"brand": "Westside", "brand_wikidata": "Q123376384"}
    api_url = "https://custom-api.westside.com/live/api/v1/store-locator"
    locations_key = "store_list"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(f"{self.api_url}/stores", callback=self.parse_states)

    def parse_states(self, response: Response) -> Iterable[JsonRequest]:
        for state in response.json()["store_state"]:
            yield JsonRequest(f"{self.api_url}/statestore?state={quote(state)}")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["store_type"] != "Westside":
            return
        item["ref"] = feature["store_code"]
        item["branch"] = re.sub(r"^Westside\s*-?\s*", "", item.pop("name"), flags=re.IGNORECASE)
        item["postcode"] = feature["store_pin_code"]
        item["phone"] = feature["store_mobile_number"]
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            if hours := feature[f"{day.lower()}_time"]:
                item["opening_hours"].add_range(day, *hours.split(" - "))
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
