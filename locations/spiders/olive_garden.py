from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class OliveGardenSpider(JSONBlobSpider):
    name = "olive_garden"
    item_attributes = {"brand": "Olive Garden", "brand_wikidata": "Q3045312"}
    allowed_domains = ["olivegarden.com"]
    locations_key = "restaurants"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://www.olivegarden.com/api/restaurants", headers={"X-Source-Channel": "WEB"})

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["contactDetail"].pop("address", {}))
        feature.pop("countryCode", None)  # internal numeric code; "country" holds the real value

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["restaurantNumber"]
        item["branch"] = feature.get("restaurantName")
        item["street_address"] = feature.get("street1")
        if phones := feature["contactDetail"].get("phoneDetail"):
            item["phone"] = phones[0].get("phoneNumber")

        item["opening_hours"] = OpeningHours()
        for day in feature.get("restaurantHours", []):
            if day.get("isRestaurantClosed"):
                item["opening_hours"].set_closed(day["day"])
                continue
            for hours_info in day.get("hoursInfo", []):
                if hours_info["name"] == "Hours of Operations":
                    item["opening_hours"].add_range(
                        day=day["day"],
                        open_time=hours_info["startTime"],
                        close_time=hours_info["endTime"],
                        time_format="%I:%M %p",
                    )

        apply_category(Categories.RESTAURANT, item)
        yield item
