import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

# Seasons 52 is a Darden brand and shares its restaurants API, the same one the
# olive_garden and longhorn_steakhouse spiders use.
#
# Postcodes arrive as nine unseparated digits, so the ZIP+4 part is split off.
#
# The API returns only the hours block covering the current day, but that block
# carries the range of days it applies to, numbered from Sunday, so the range
# is expanded rather than recording a single day.

DAYS_BY_NUMBER = {1: "Su", 2: "Mo", 3: "Tu", 4: "We", 5: "Th", 6: "Fr", 7: "Sa"}


class Seasons52USSpider(JSONBlobSpider):
    name = "seasons_52_us"
    item_attributes = {"brand": "Seasons 52", "brand_wikidata": "Q7441933"}
    allowed_domains = ["seasons52.com"]
    requires_proxy = True
    locations_key = "restaurants"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://www.seasons52.com/api/restaurants", headers={"X-Source-Channel": "WEB"})

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["contactDetail"].pop("address", {}))
        feature.pop("countryCode", None)  # internal numeric code; "country" holds the real value

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["restaurantNumber"]
        item["branch"] = feature.get("restaurantName")
        item["street_address"] = feature.get("street1")
        if phones := feature["contactDetail"].get("phoneDetail"):
            item["phone"] = phones[0].get("phoneNumber")
        # "480844768" is 48084-4768.
        if postcode := re.fullmatch(r"(\d{5})(\d{4})", item.get("postcode") or ""):
            item["postcode"] = "-".join(postcode.groups())

        item["opening_hours"] = OpeningHours()
        for day in feature.get("restaurantHours", []):
            if day.get("isRestaurantClosed"):
                item["opening_hours"].set_closed(day["day"])
                continue
            for hours_info in day.get("hoursInfo", []):
                if hours_info["name"] != "Hours of Operations":
                    continue
                start = DAYS_BY_NUMBER.get(hours_info.get("dayOfWeek"))
                end = DAYS_BY_NUMBER.get(hours_info.get("endDayOfWeek"), start)
                if not start:
                    continue
                item["opening_hours"].add_days_range(
                    day_range(start, end),
                    hours_info["startTime"],
                    hours_info["endTime"],
                    time_format="%I:%M %p",
                )

        apply_category(Categories.RESTAURANT, item)
        yield item
