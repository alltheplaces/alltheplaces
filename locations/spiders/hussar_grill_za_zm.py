from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature, SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider

ATTRIBUTE_EXTRAS = {
    "Wifi": (Extras.WIFI, False),
    "Halal food": (Extras.HALAL, False),
    "Takeaway": (Extras.TAKEAWAY, False),
    "Delivery": (Extras.DELIVERY, False),
    "Play area": (Extras.KIDS_AREA, False),
    "Dine-in": (Extras.INDOOR_SEATING, False),
    "Smoking Section": (Extras.SMOKING_AREA, True),
    "Wheelchair Accessible": (Extras.WHEELCHAIR, True),
}


class HussarGrillZAZMSpider(JSONBlobSpider):
    name = "hussar_grill_za_zm"
    item_attributes = {
        "brand": "The Hussar Grill",
        "brand_wikidata": "Q130232305",
    }
    allowed_domains = ["hussargrill.co.za"]
    start_urls = ("https://hussargrill.co.za/api/gostoreall",)
    locations_key = ["res", "stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        attributes = {
            attribute["name"]: attribute.get("value")
            for attribute in feature.get("attributes", [])
            if attribute.get("name") is not None
        }

        item["ref"] = feature.get("location_code")
        item["branch"] = item.pop("name").removeprefix("The Hussar Grill ")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            if not (day_hours := feature.get(day.lower())):
                continue
            if day_hours.get("all_day") is True:
                item["opening_hours"].add_range(day, "00:00", "23:59")
                continue
            item["opening_hours"].add_range(day, day_hours.get("open"), day_hours.get("close"), "%H:%M:%S")

        if tripadvisor_url := feature.get("tripadvisor_url") or attributes.get("Trip Advisor URL"):
            set_social_media(item, SocialMedia.TRIPADVISOR, tripadvisor_url)
        if instagram_url := feature.get("instagram_url"):
            set_social_media(item, SocialMedia.INSTAGRAM, instagram_url)

        for attribute_name, (extra, apply_positive_only) in ATTRIBUTE_EXTRAS.items():
            if attribute_name in attributes:
                apply_yes_no(extra, item, attributes[attribute_name] is True, apply_positive_only)

        yield item
