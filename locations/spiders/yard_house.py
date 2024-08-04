import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


def slugify(s):
    return re.sub(r"[^\w]+", "-", s, count=0).lower()


class YardHouseSpider(Spider):
    name = "yard_house"
    item_attributes = {"brand": "Yard House", "brand_wikidata": "Q21189156"}

    def start_requests(self):
        yield JsonRequest("https://www.yardhouse.com/api/restaurants", headers={"x-source-channel": "WEB"})

    def parse(self, response):
        for location in response.json()["restaurants"]:
            item = DictParser.parse(location["contactDetail"]["address"])
            item["ref"] = location["restaurantNumber"]
            item["branch"] = location["restaurantName"]
            item["phone"] = location["contactDetail"]["phoneDetail"][0]["phoneNumber"]
            item["street_address"] = merge_address_lines(
                [location["contactDetail"]["address"]["street1"], location["contactDetail"]["address"].get("street2")]
            )
            item["country"] = location["contactDetail"]["address"]["country"]
            item["extras"]["start_date"] = location["restaurantOpenDate"]
            # Opening hours are only today's

            apply_yes_no(
                Extras.TAKEAWAY,
                item,
                location["features"].get("isRestaurantTogoEnabled")
                or location["features"].get("onlineTogoEnabled")
                or location["features"].get("curbSideTogoEnabled"),
            )
            apply_yes_no(
                Extras.OUTDOOR_SEATING,
                item,
                any(amenity["title"] == "Patio seating available" for amenity in location["amenities"]),
            )
            apply_yes_no(Extras.WIFI, item, any(amenity["title"] == "Free WiFi" for amenity in location["amenities"]))

            item["website"] = (
                f"https://www.yardhouse.com/locations/{slugify(item['state'])}/{slugify(item['city'])}/{slugify(item['branch'])}/{item['ref']}"
            )

            # Note: Not reliable (especially when there's more than one location in the city)
            item["image"] = (
                f"https://media.yardhouse.com/en_us/images/marketing/{slugify(item['city'])}-{slugify(item['state'])}-yard-house-599x430.jpg.jpg"
            )

            yield item
