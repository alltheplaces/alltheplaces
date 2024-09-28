import json
from typing import Any, Iterable
from urllib.parse import urlencode

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.categories import Drink, Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import clean_facebook

GOOGLE_ATTRIBUTES_MAP = {
    "accepts_reservations": Extras.RESERVATION,
    "has_bar_onsite": Extras.BAR,
    "has_delivery": Extras.DELIVERY,
    "has_drive_through": Extras.DRIVE_THROUGH,
    "has_high_chairs": Extras.HIGH_CHAIR,
    "has_live_music": Extras.LIVE_MUSIC,
    "has_restroom": Extras.TOILETS,
    "has_seating_outdoors": Extras.OUTDOOR_SEATING,
    "has_takeout": Extras.TAKEAWAY,
    "has_wheelchair_accessible_restroom": Extras.TOILETS_WHEELCHAIR,
    "has_wheelchair_accessible_parking": Extras.PARKING_WHEELCHAIR,
    "pay_check": PaymentMethods.CHEQUE,
    "pay_debit_card": PaymentMethods.DEBIT_CARDS,
    "pay_mobile_nfc": PaymentMethods.CONTACTLESS,
    "pay_credit_card": PaymentMethods.CREDIT_CARDS,
    "requires_cash_only": PaymentMethods.CASH_ONLY,
    "requires_reservations": Extras.RESERVATION_REQUIRED,
    "serves_vegetarian": Extras.VEGETARIAN,
    "serves_halal_food": Extras.HALAL,
    "serves_liquor": Drink.LIQUOR,
    "serves_coffee": Drink.COFFEE,
    "serves_cocktails": Drink.COCKTAIL,
    "serves_beer": Drink.BEER,
    "serves_wine": Drink.WINE,
    "welcomes_dogs": Extras.DOG,
}

GOOGLE_WHEELCHAIR_KEYS = [
    "has_wheelchair_accessible_restroom",
    "has_wheelchair_accessible_entrance",
    "has_wheelchair_accessible_seating",
]


class YextAnswersSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "yext"}
    endpoint: str = "https://liveapi.yext.com/v2/accounts/me/answers/vertical/query"
    api_key: str = ""
    experience_key: str = ""
    api_version: str = "20220511"
    page_limit: int = 50
    locale: str = "en"
    environment: str = "PRODUCTION"  # "STAGING" also used
    feature_type: str = "locations"  # "restaurants" also used
    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/[A-Za-z0-9\-.]+\.yext(?:apis)?\.com\/v2\/accounts\/me\/search\/vertical\/query\?.*?(?<=[?&])api_key=(?P<api_key>[0-9a-f]{32})(?:&|$)"
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/[A-Za-z0-9\-.]+\.yext(?:apis)?\.com\/v2\/accounts\/me\/search\/vertical\/query\?.*?(?<=[?&])experienceKey=(?P<experience_key>\w+)(?:&|$)"
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/[A-Za-z0-9\-.]+\.yext(?:apis)?\.com\/v2\/accounts\/me\/search\/vertical\/query\?.*?(?<=[?&])v=(?P<api_version>\d{8})(?:&|$)"
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/[A-Za-z0-9\-.]+\.yext(?:apis)?\.com\/v2\/accounts\/me\/search\/vertical\/query\?.*?(?<=[?&])locale=(?P<locale>\w+)(?:&|$)"
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/[A-Za-z0-9\-.]+\.yext(?:apis)?\.com\/v2\/accounts\/me\/search\/vertical\/query\?.*?(?<=[?&])version=(?P<environment>\w+)(?:&|$)"
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/[A-Za-z0-9\-.]+\.yext(?:apis)?\.com\/v2\/accounts\/me\/search\/vertical\/query\?.*?(?<=[?&])verticalKey=(?P<feature_type>\w+)(?:&|$)"
        ),
    ]

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url="{}?{}".format(
                self.endpoint,
                urlencode(
                    {
                        "experienceKey": self.experience_key,
                        "api_key": self.api_key,
                        "v": self.api_version,
                        "version": self.environment,
                        "locale": self.locale,
                        "verticalKey": self.feature_type,
                        "filters": json.dumps(
                            {"builtin.location": {"$near": {"lat": 0, "lng": 0, "radius": 50000000}}}
                        ),
                        "limit": str(self.page_limit),
                        "offset": str(offset),
                        "source": "STANDARD",
                    }
                ),
            ),
            meta={"offset": offset},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["results"]:
            location = location["data"]
            item = DictParser.parse(location)
            item["branch"] = location.get("geomodifier")

            phones = []
            for phone_type in ["localPhone", "mainPhone", "mobilePhone"]:
                if phone := location.get(phone_type):
                    if isinstance(phone, dict):
                        phones.append(phone.get("number"))
                    elif isinstance(phone, str):
                        phones.append(phone)
            if len(phones) > 0:
                item["phone"] = "; ".join(phones)

            if emails := location.get("emails"):
                item["email"] = "; ".join(emails)

            item["extras"]["ref:google"] = location.get("googlePlaceId")
            item["twitter"] = location.get("twitterHandle")
            item["extras"]["contact:instagram"] = location.get("instagramHandle")
            if "facebookVanityUrl" in location:
                item["facebook"] = clean_facebook(location["facebookVanityUrl"])
            else:
                item["facebook"] = clean_facebook(location.get("facebookPageUrl"))

            if website_url_dict := location.get("websiteUrl"):
                if website_url_dict.get("preferDisplayUrl"):
                    item["website"] = website_url_dict.get("displayUrl")
                else:
                    item["website"] = website_url_dict.get("url")

            if menu_url_dict := location.get("menuUrl"):
                if menu_url_dict.get("preferDisplayUrl"):
                    item["extras"]["website:menu"] = menu_url_dict.get("displayUrl")
                else:
                    item["extras"]["website:menu"] = menu_url_dict.get("url")

            item["opening_hours"] = self.parse_opening_hours(location.get("hours"))
            item["extras"]["opening_hours:delivery"] = self.parse_opening_hours(location.get("deliveryHours"))

            self.parse_payment_methods(location, item)
            self.parse_google_attributes(location, item)

            yield from self.parse_item(location, item) or []

        if len(response.json()["response"]["results"]) == self.page_limit:
            yield self.make_request(response.meta["offset"] + self.page_limit)

    def parse_opening_hours(self, hours: dict, **kwargs: Any) -> OpeningHours | None:
        oh = OpeningHours()
        if not hours:
            return None
        for day, rule in hours.items():
            if not isinstance(rule, dict):
                continue
            if day == "holidayHours":
                continue
            if rule.get("isClosed") is True:
                oh.set_closed(day)
                continue
            for time in rule["openIntervals"]:
                oh.add_range(day, time["start"], time["end"])

        return oh.as_opening_hours()

    def parse_payment_methods(self, location: dict, item: Feature) -> None:
        if payment_methods := location.get("paymentOptions"):
            payment_methods = [p.lower().replace(" ", "") for p in payment_methods]
            apply_yes_no(PaymentMethods.ALIPAY, item, "alipay" in payment_methods)
            apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "americanexpress" in payment_methods)
            apply_yes_no(PaymentMethods.APPLE_PAY, item, "applepay" in payment_methods)
            apply_yes_no(PaymentMethods.CASH, item, "cash" in payment_methods)
            apply_yes_no(PaymentMethods.CHEQUE, item, "check" in payment_methods)
            apply_yes_no(PaymentMethods.CONTACTLESS, item, "contactlesspayment" in payment_methods)
            apply_yes_no(PaymentMethods.DINERS_CLUB, item, "dinersclub" in payment_methods)
            apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "discover" in payment_methods)
            apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "googlepay" in payment_methods)
            apply_yes_no(PaymentMethods.MASTER_CARD, item, "mastercard" in payment_methods)
            apply_yes_no(PaymentMethods.SAMSUNG_PAY, item, "samsungpay" in payment_methods)
            apply_yes_no(PaymentMethods.UNIONPAY, item, "chinaunionpay" in payment_methods)
            apply_yes_no(PaymentMethods.VISA, item, "visa" in payment_methods)
            apply_yes_no(PaymentMethods.WECHAT, item, "wechatpay" in payment_methods)

    def parse_google_attributes(self, location: dict, item: Feature) -> None:
        if google_attributes := location.get("googleAttributes"):
            for key, attribute in GOOGLE_ATTRIBUTES_MAP.items():
                if key in google_attributes:
                    apply_yes_no(attribute, item, google_attributes[key][0] == "true", False)
            wheelchair_keys_present = [key for key in GOOGLE_WHEELCHAIR_KEYS if key in google_attributes]
            if all([google_attributes[key][0] == "true" for key in wheelchair_keys_present]):
                apply_yes_no(Extras.WHEELCHAIR, item, True, False)
            elif any([google_attributes[key][0] == "true" for key in wheelchair_keys_present]):
                apply_yes_no(Extras.WHEELCHAIR_LIMITED, item, True, False)
            else:
                apply_yes_no(Extras.WHEELCHAIR, item, True, False)

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        yield item
