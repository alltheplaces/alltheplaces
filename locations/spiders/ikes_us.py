import json
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Drink, Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import SocialMedia, set_social_media

ATTRIBUTE_MAP = {
    Extras.HALAL: ["serves_halal_food"],
    Extras.WHEELCHAIR: ["has_wheelchair_accessible_seating"],
    Extras.RESERVATION_REQUIRED: ["requires_reservations"],
    Drink.COCKTAIL: ["serves_cocktails"],
    Extras.DOG: ["welcomes_dogs", "allows_dogs_inside"],
    Extras.RESERVATION: ["accepts_reservations"],
    Extras.TOILETS: ["has_restroom"],
    Extras.VEGETARIAN: ["serves_vegetarian"],
    Extras.BRUNCH: ["serves_brunch"],
    Extras.LUNCH: ["serves_lunch"],
    Extras.BREAKFAST: ["serves_breakfast"],
    Extras.HIGH_CHAIR: ["has_high_chairs"],
    Extras.TAKEAWAY: ["has_takeout"],
    Extras.LIVE_MUSIC: ["has_live_music"],
    Drink.BEER: ["serves_beer"],
    Extras.DRIVE_THROUGH: ["has_drive_through"],
    Extras.OUTDOOR_SEATING: ["has_seating_outdoors", "has_seating_rooftop"],
    Extras.INDOOR_SEATING: ["serves_dine_in"],
    Extras.TOILETS_WHEELCHAIR: ["has_wheelchair_accessible_restroom"],
    Drink.COFFEE: ["serves_coffee"],
    Drink.WINE: ["serves_wine"],
    Drink.LIQUOR: ["serves_liquor"],
    Extras.VEGAN: ["serves_vegan"],
    Extras.WIFI: ["wi_fi"],
    Extras.BABY_CHANGING_TABLE: ["has_changing_tables"],
    Extras.DELIVERY: ["has_delivery"],
    PaymentMethods.CONTACTLESS: ["pay_mobile_nfc"],
    PaymentMethods.CASH_ONLY: ["requires_cash_only"],
    PaymentMethods.CREDIT_CARDS: ["pay_credit_card"],
    PaymentMethods.DEBIT_CARDS: ["pay_debit_card"],
}


class IkesUSSpider(Spider):
    name = "ikes_us"
    item_attributes = {"brand": "Ike's Love and Sandwiches", "brand_wikidata": "Q112028897"}

    async def start(self) -> AsyncIterator[Request]:
        body = json.dumps(
            {
                "request": {
                    "appkey": "EE7039D8-2B5A-11EE-9FA4-F2C3D2F445A6",
                    "formdata": {
                        "geoip": False,
                        "order": "city",
                        "objectname": "Locator::Store",
                        "limit": 1000,
                        "dataview": "store_default",
                        "false": "0",
                    },
                }
            }
        )
        yield Request(
            url="https://locations.ikessandwich.com/rest/getlist?lang=en_US&isSOCiLocator=true",
            method="POST",
            body=body,
            callback=self.parse,
        )

    def parse(self, response: Response) -> Any:
        data = response.json().get("response", {}).get("collection", [])
        for location in data:
            item = DictParser.parse(location)
            item["ref"] = location.get("uid")
            item["branch"] = item.pop("name", "")

            if openDate := location.get("openDate"):
                item["extras"]["start_date"] = openDate

            if yelpUrl := location.get("yelp_url"):
                set_social_media(item, SocialMedia.YELP, yelpUrl)

            attributes = location.get("location", {}).get("attributes", {})

            for extra, keys in ATTRIBUTE_MAP.items():
                values = [attributes.get(key) for key in keys]
                if "yes" in values:
                    apply_yes_no(extra, item, True, apply_positive_only=False)
                elif "no" in values:
                    apply_yes_no(extra, item, False, apply_positive_only=False)

            item["extras"]["website:menu"] = attributes.get("url_menu")

            payment_forms = location.get("location", {}).get("payment_forms", [])
            apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "American Express" in payment_forms)
            apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "Discover" in payment_forms)
            apply_yes_no(PaymentMethods.CASH, item, "Cash" in payment_forms)
            apply_yes_no(PaymentMethods.VISA, item, "Visa" in payment_forms)
            apply_yes_no(PaymentMethods.MASTER_CARD, item, "Mastercard" in payment_forms)

            hours = location.get("location", {}).get("hours", {})
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if day.lower() in hours:
                    for time_range in hours[day.lower()]:
                        open_time, close_time = time_range.split("-")
                        item["opening_hours"].add_range(day=day[:2], open_time=open_time, close_time=close_time)

            self.post_cleaning(item)
            yield item

    def post_cleaning(self, item: dict) -> None:
        if "website" in item and not item["website"].startswith("http"):
            item["website"] = "https://" + item["website"]
