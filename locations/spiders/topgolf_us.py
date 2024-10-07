import json
from urllib.parse import urlparse

from scrapy import Request

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider


def get_username(url):
    path = urlparse(url).path.lstrip("/")
    if "/" in path:
        path = path[: path.find("/")]
    return path


class TopgolfUSSpider(JSONBlobSpider):
    name = "topgolf_us"
    item_attributes = {"brand": "Topgolf", "brand_wikidata": "Q7824379"}
    start_urls = ["https://topgolf.com/us/"]
    locations_key = ["pageProps", "locations", "data"]

    def parse(self, response):
        # Fetch the build ID
        build_id = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["buildId"]
        # Some location data is available in __NEXT_DATA__, but locations.json also includes e.g. amenities and opening hours
        yield Request(f"https://topgolf.com/_next/data/{build_id}/us/locations.json", callback=self.parse_locations)

    def parse_locations(self, response):
        yield from super().parse(response)

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")

        item["website"] = f"https://topgolf.com/us/{location['alias']}/"
        if location["upcoming"]:
            item["extras"]["start_date"] = location["upcoming_date"]
        item["extras"]["website:menu"] = "https://s3.topgolf.com/" + location["food_menu"]
        if (social := get_username(location["twitter"])) != "topgolf":
            set_social_media(item, SocialMedia.TWITTER, social)
        if (social := get_username(location["youtube"])) != "topgolf":
            set_social_media(item, SocialMedia.YOUTUBE, social)
        if (social := get_username(location["instagram"])) != "topgolf":
            set_social_media(item, SocialMedia.INSTAGRAM, social)
        if (social := get_username(location["facebook"])) != "topgolf":
            set_social_media(item, SocialMedia.FACEBOOK, social)
        if location.get("gallery"):
            item["image"] = location["gallery"][0]["large"]

        amenities = {a["amenity"] for a in location.get("amenities", [])}
        if 19 in amenities:
            # "3 floors"
            item["extras"]["building:levels"] = 3
        if 20 in amenities:
            # "2 floors"
            item["extras"]["building:levels"] = 2
        if 21 in amenities:
            # "1 floor"
            item["extras"]["building:levels"] = 1
        if 15 in amenities:
            # "120 all-weather bays"
            item["extras"]["rooms"] = 120
        if 14 in amenities:
            # "100+ all-weather bays"
            item["extras"]["rooms"] = 100
        if 12 in amenities:
            # "90+ all-weather bays"
            item["extras"]["rooms"] = 90
        if 2 in amenities:
            # "70+ all-weather bays"
            item["extras"]["rooms"] = 70
        if 127 in amenities:
            # "60 all-weather bays"
            item["extras"]["rooms"] = 60
        if 67 in amenities:
            # "50+ all-weather bays"
            item["extras"]["rooms"] = 50
        if 102 in amenities:
            # "44 all-weather bays"
            item["extras"]["rooms"] = 44
        if 16 in amenities:
            # "30+ all-weather bays"
            item["extras"]["rooms"] = 30
        if 30 in amenities:
            # "48-foot video wall"
            item["extras"]["screens"] = 1
        if 157 in amenities:
            # "36-foot video wall and 200+ HDTVs"
            item["extras"]["screens"] = 200
        if 152 in amenities:
            # "28-foot video wall and 200+ HDTVs"
            item["extras"]["screens"] = 200
        if 142 in amenities:
            # "22-foot video wall and 100+ HDTVs"
            item["extras"]["screens"] = 100
        if 17 in amenities:
            # "13-foot video wall and 50+ HDTVs"
            item["extras"]["screens"] = 50
        if 5 in amenities:
            # "Over 200 HDTVs"
            item["extras"]["screens"] = 200
        apply_yes_no(Extras.WIFI, item, 18 in amenities)  # "Free Wi-Fi"
        apply_yes_no("restaurant", item, 9 in amenities)  # "Bar & restaurant"

        oh = OpeningHours()
        for day_idx, hours in enumerate(location["hours"]["hours"]):
            oh.add_range(DAYS_3_LETTERS_FROM_SUNDAY[day_idx], hours["time_start"], hours["time_end"])
        item["opening_hours"] = oh

        yield item
