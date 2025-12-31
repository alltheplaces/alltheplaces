from typing import AsyncIterator

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import Request

from locations.hours import DAYS, OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.state_clean_up import US_TERRITORIES


class XfinitySpider(Spider):
    name = "xfinity"
    item_attributes = {"brand": "Xfinity", "brand_wikidata": "Q5151002"}
    allowed_domains = ["www.xfinity.com", "api-support.xfinity.com"]

    async def start(self) -> AsyncIterator[Request]:
        for state in GeonamesCache().get_us_states() | US_TERRITORIES:
            yield Request(url=f"https://api-support.xfinity.com/servicecenters?location={state}")

    def store_hours(self, rules: str) -> OpeningHours:
        if not rules:
            return
        oh = OpeningHours()
        for rule in rules.split(","):
            day, start_hour, start_mins, end_hour, end_mins = rule.split(":")
            oh.add_range(DAYS[int(day) - 2], f"{start_hour}:{start_mins}", f"{end_hour}:{end_mins}")
        return oh

    def parse(self, response):
        for store in response.json()["locations"]:
            if store["locationName"].startswith("Comcast Service Center"):
                continue
            properties = {
                "ref": store["id"],
                "opening_hours": self.store_hours(store["hours"]),
                "lat": store["yextDisplayLat"],
                "lon": store["yextDisplayLng"],
                "street_address": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": response.json()["geo"]["country"],
                "website": store["websiteUrl"].split("?")[0],
            }
            item = Feature(**properties)

            if store["locationName"].lower().endswith(" - closed"):
                set_closed(item)

            # TODO: hours

            yield item
