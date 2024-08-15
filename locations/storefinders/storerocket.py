from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature, SocialMedia, set_social_media


class StoreRocketSpider(Spider):
    """
    StoreRocket is a map based JSON API driven store locator.
    https://storerocket.io/

    To use, specify the `storerocket_id` and optionally `base_url` to set website attributes.
    """

    dataset_attributes = {"source": "api", "api": "storerocket.io"}
    storerocket_id: str = ""
    base_url: str | None = None

    def start_requests(self):
        yield JsonRequest(url=f"https://storerocket.io/api/user/{self.storerocket_id}/locations")

    def parse(self, response, **kwargs):
        if not response.json()["success"]:
            return

        for location in response.json()["results"]["locations"]:
            item = DictParser.parse(location)

            item["street_address"] = ", ".join(filter(None, [location["address_line_1"], location["address_line_2"]]))
            item["email"] = location.get("email")

            set_social_media(item, SocialMedia.FACEBOOK, location.get("facebook"))
            set_social_media(item, SocialMedia.INSTAGRAM, location.get("instagram"))
            set_social_media(item, SocialMedia.TWITTER, location.get("twitter"))

            if self.base_url:
                item["website"] = f'{self.base_url}?location={location["slug"]}'

            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_name, day_hours in location["hours"].items():
                hours_string = hours_string + f" {day_name}: {day_hours}"
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
