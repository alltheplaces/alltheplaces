import datetime

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.structured_data_spider import clean_facebook

# Documentation for the Yext API is available at:
# 1. https://hitchhikers.yext.com/docs/contentdeliveryapis/introduction/overview-policies-and-conventions/
# 2. https://hitchhikers.yext.com/docs/contentdeliveryapis/legacy/entities
#
# Note that there is a legacy "locations" API and additionally a legacy domain for the API, "liveapi.yext.com".
# You can use the API key from these URLs with this spider.
#
# To use this spider, simply specify a valid api_key variable. You may need to define a parse_item function
# to extract additional location data and to make corrections to automatically extracted location data.


class YextSpider(Spider):
    dataset_attributes = {"source": "api", "api": "yext"}

    api_key: str = ""
    api_version: str = ""
    search_filter: str = "{}"
    page_limit: int = 50
    wanted_types: list[str] = ["location"]

    def request_page(self, next_offset):
        yield JsonRequest(
            url=f"https://cdn.yextapis.com/v2/accounts/me/entities?api_key={self.api_key}&v={self.api_version}&limit={self.page_limit}&offset={next_offset}&filter={self.search_filter}",
            meta={"offset": next_offset},
        )

    def start_requests(self):
        if not self.api_version:
            now = datetime.datetime.now()
            self.api_version = now.strftime("%Y%m%d")
        yield from self.request_page(0)

    def parse(self, response):
        for location in response.json()["response"]["entities"]:
            if location["meta"].get("entityType") and location["meta"].get("entityType") not in self.wanted_types:
                continue
            if location.get("closed") or "CLOSED" in location["name"].upper():
                continue
            item = DictParser.parse(location)
            item["ref"] = location["meta"]["id"]
            if not item["lat"] and not item["lon"] and "yextDisplayCoordinate" in location:
                item["lat"] = location["yextDisplayCoordinate"]["latitude"]
                item["lon"] = location["yextDisplayCoordinate"]["longitude"]
            item["street_address"] = " ".join(
                filter(None, [location["address"].get("line1"), location["address"].get("line2")])
            )
            if "websiteUrl" in location:
                item["website"] = location["websiteUrl"].get("url")
            if "emails" in location:
                item["email"] = location["emails"][0]
            item["phone"] = location.get("mainPhone")
            item["twitter"] = location.get("twitterHandle")
            item["extras"]["contact:instagram"] = location.get("instagramHandle")
            if "facebookVanityUrl" in location:
                item["facebook"] = clean_facebook(location["facebookVanityUrl"])
            else:
                item["facebook"] = clean_facebook(location.get("facebookPageUrl"))

            if "hours" in location:
                item["opening_hours"] = OpeningHours()
                for day_name, day_intervals in location["hours"].items():
                    if day_name == "holidayHours":
                        continue
                    if "isClosed" in day_intervals and day_intervals["isClosed"]:
                        continue
                    if "openIntervals" not in day_intervals:
                        continue
                    for interval in day_intervals["openIntervals"]:
                        item["opening_hours"].add_range(day_name.title(), interval["start"], interval["end"])

            yield from self.parse_item(item, location) or []

        next_offset = response.meta["offset"] + self.page_limit
        if next_offset < response.json()["response"]["count"]:
            yield from self.request_page(next_offset)

    def parse_item(self, item, location, **kwargs):
        yield item
