import uuid
from typing import Any, AsyncIterator

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BuffaloWildWingsUSSpider(Spider):
    name = "buffalo_wild_wings_us"
    item_attributes = {"brand": "Buffalo Wild Wings", "brand_wikidata": "Q509255"}

    async def start(self) -> AsyncIterator[Any]:
        for state_code in GeonamesCache().get_us_states().keys():
            yield JsonRequest(
                url=f"https://api-idp.buffalowildwings.com/bww/digital-exp-api/v1/locations/regions?regionCode={state_code}&countryCode=US",
                headers={
                    "Origin": "https://www.buffalowildwings.com",
                    "Referer": "https://www.buffalowildwings.com/",
                    "X-Session-Id": str(uuid.uuid4()),
                    "X-Channel": "WEBOA",
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not response.json()["locations"]:
            return
        for city in response.json()["locations"][0]["regions"][0]["cities"]:
            for restaurant in city["locations"]:
                item = DictParser.parse(restaurant["contactDetails"])
                item["ref"] = restaurant["id"]
                item["branch"] = restaurant["displayName"]
                item["lat"] = restaurant["geoDetails"]["latitude"]
                item["lon"] = restaurant["geoDetails"]["longitude"]
                item["opening_hours"] = parse_opening_hours(restaurant["locationHours"])
                yield item


def parse_opening_hours(locationHours):
    oh = OpeningHours()

    for entry in locationHours:
        day = entry.get("dayOfWeek")

        if entry.get("isTwentyFourHourService"):
            oh.add_range(day=day, open_time="00:00", close_time="24:00")
            continue

        open_time = entry.get("startTime").strip()[:5]
        close_time = entry.get("endTime").strip()[:5]

        if close_time == "00:00":
            close_time = "24:00"

        oh.add_range(day=day, open_time=open_time, close_time=close_time)

    return oh
