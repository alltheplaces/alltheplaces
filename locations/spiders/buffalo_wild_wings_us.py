import uuid

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BuffaloWildWingsUSSpider(Spider):
    name = "buffalo_wild_wings_us"
    item_attributes = {"brand": "Buffalo Wild Wings", "brand_wikidata": "Q509255"}

    # All US states and D.C.
    state_codes = [
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    ]

    def start_requests(self):
        for state_code in self.state_codes:
            yield JsonRequest(
                url=f"https://api-idp.buffalowildwings.com/bww/digital-exp-api/v1/locations/regions?regionCode={state_code}&countryCode=US",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Origin": "https://www.buffalowildwings.com",
                    "Referer": "https://www.buffalowildwings.com/",
                    "User-Agent": "Mozilla/5.0",
                    "X-Session-Id": str(uuid.uuid4()),
                    "X-Channel": "WEBOA",
                },
                callback=self.parse_region,
            )

    def parse_region(self, response):
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
    day_map = {
        "MONDAY": "Mo",
        "TUESDAY": "Tu",
        "WEDNESDAY": "We",
        "THURSDAY": "Th",
        "FRIDAY": "Fr",
        "SATURDAY": "Sa",
        "SUNDAY": "Su",
    }

    oh = OpeningHours()

    for entry in locationHours:
        day = day_map.get(entry.get("dayOfWeek"))

        if entry.get("isTwentyFourHourService"):
            oh.add_range(day=day, open_time="00:00", close_time="24:00")
            continue

        open_time = entry.get("startTime").strip()[:5]
        close_time = entry.get("endTime").strip()[:5]

        if close_time == "00:00":
            close_time = "24:00"

        oh.add_range(day=day, open_time=open_time, close_time=close_time)

    return oh.as_opening_hours()
