from scrapy import Selector, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

# The archived official home page of this Localisr store finder is:
# https://web.archive.org/web/20231021142419/https://matterdesign.com.au/localisr-a-geolocation-powered-store-finder-for-bigcommerce/
#
# It appears this store finder may be deprecated and is in the process of
# being replaced as some brands previously making API calls to
# app.localisr.io are now making different API calls to
# <brand_key>.matter.design. The brand store locator pages still pull in
# Javascript from app.localisr.io and the app.localisr.io API calls still
# work, so for these brands, LocalisrSpider still appears to work, but
# probably should be replaced.
#
# Documentation does not appear to be publicly available, however
# the obersved behaviour is that coordinates are supplied for
# searching with a given radius. Often this radius appears to be
# ignored and all locations are returned at once.
#
# To use this spider, specify the api_key. Then add to the search_coordinates
# array one or more tuples of coordinates as (lat, lon) which will be
# searched with the provided value of search_radius (default is 400). If for
# some reason you find a consumer of this API with a small allowed
# search_radius or many coordinates needing to be searched, override the
# start_requests function to populate the search_coordinates array and then
# call super().start_requests() to start the scraping.
#
# If you need to clean up data returned, override the parse_item function.


class LocalisrSpider(Spider):
    dataset_attributes = {"source": "api", "api": "localisr.io"}
    api_key: str = ""
    api_version: str = "2.1.0"  # Use the latest observed API version by default
    search_coordinates: list[tuple[float, float]] = []
    search_radius: int = 400

    def start_requests(self):
        data = {
            "key": self.api_key,
            "version": self.api_version,
        }
        yield JsonRequest(
            url="https://app.localisr.io/api/auth/v2/validate?type=&view=all&map_permission=false&map_trigger=initial",
            data=data,
            method="POST",
            callback=self.parse_session_token,
        )

    def parse_session_token(self, response: Response):
        request_token = response.json()["data"]["request_token"]
        user_token = (
            Selector(text=response.json()["data"]["builder"]).xpath('//input[@id="slmUniqueUserToken"]/@value').get()
        )
        for search_coordinate in self.search_coordinates:
            url = f"https://app.localisr.io/api/v1/collection?lat={search_coordinate[0]}&lng={search_coordinate[1]}&radius={self.search_radius}&type=&view=all&map_permission=false&map_trigger=search"
            headers = {
                "SLM-Request-Token": request_token,
                "SLM-Unique-User-Token": user_token,
            }
            yield JsonRequest(url=url, headers=headers, method="GET", callback=self.parse)

    def parse(self, response: Response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["store_identifier"]
            item["housenumber"] = location["location"].get("street_number")
            item["street"] = location["location"].get("street_name")
            item["city"] = location["location"].get("suburb")
            if not item["city"]:
                item["city"] = location["location"].get("city")
            item["postcode"] = location["location"].get("postcode")
            item["state"] = location["location"].get("state")
            item["country"] = location["location"].get("country")
            item["addr_full"] = location["location"].get("address")
            item["street_address"] = ", ".join(
                filter(None, [location["location"].get("address_1"), location["location"].get("address_2")])
            )
            item["phone"] = location["store"].get("phone")
            item["email"] = location["store"].get("email")
            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in location["store"].get("timetable").items():
                if not day_hours:
                    continue
                item["opening_hours"].add_range(day_name, day_hours[0].upper(), day_hours[1].upper(), "%I:%M %p")
            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict):
        yield item
