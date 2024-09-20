from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import SocialMedia, set_social_media


class TogosUSSpider(Spider):
    name = "togos_us"
    item_attributes = {"brand": "Togo's", "brand_wikidata": "Q3530375"}
    start_urls = [
        "https://www.togos.com/locations/getLocationJson?"
        "northEastLat=90&"
        "northEastLng=180&"
        "northWestLat=90&"
        "northWestLng=-180&"
        "southEastLat=-90&"
        "southEastLng=180&"
        "southWestLat=-90&"
        "southWestLng=-180"
    ]

    def parse(self, response):
        for location in response.json()["markers"]:
            if location.get("opening") == "Closed":
                continue

            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["website"] = location["fields"].get("website")
            item["extras"]["website:menu"] = location["fields"].get("menu_url")
            set_social_media(item, SocialMedia.FACEBOOK, location["facebook_url"])
            set_social_media(item, SocialMedia.YELP, location["yelp_url"])

            oh = OpeningHours()
            for day_hours in location["hours"].split(";"):
                if day_hours.count(",") != 2:
                    continue
                day, open_time, close_time = day_hours.split(",")
                oh.add_range(DAYS[int(day) - 1], open_time, close_time, time_format="%H%M")
            item["opening_hours"] = oh

            yield item
