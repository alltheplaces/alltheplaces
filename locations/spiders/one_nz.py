from typing import AsyncIterator, Iterable
from uuid import uuid4

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class OneNZSpider(JSONBlobSpider):
    name = "one_nz"
    item_attributes = {"brand": "One NZ", "brand_wikidata": "Q7939291"}
    interaction_id = str(uuid4())
    locations_key = ["locations"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.public.one.nz/vf/public/eshop-store-locator-rest/v1/stores/locations",
            headers={"x-correlation-id": self.interaction_id, "x-source": "ESHOP", "x-channel-id": "ONLINE"},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["latlng"]["latitude"], feature["latlng"]["longitude"]
        item["branch"] = item.pop("name").removeprefix("One NZ ")
        item["street_address"] = feature["address"]["addressLines"][0]
        item["ref"] = feature["storeCode"]
        if feature["phoneNumber"] == "0800 800 021":
            item["phone"] = ""
        try:
            item["opening_hours"] = self.parse_opening_hours(feature["regularHours"])
        except ValueError:
            self.log("Error parsing opening hours: {}".format(feature["regularHours"]))

        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item

    def parse_opening_hours(self, business_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            rule = business_hours[day.lower()]
            if rule["timePeriods"] == []:
                oh.set_closed(day)
            else:
                for periods in rule["timePeriods"]:
                    oh.add_range(day, periods["open"], periods["close"], "%H:%M")
        return oh
