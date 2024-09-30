from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class AmrestEUSpider(Spider, AutomaticSpiderGenerator):
    """
    AmRest is a European multinational casual dining, fast-food restaurant and coffee shop operator headquartered in the Spanish capital, Madrid
    https://www.wikidata.org/wiki/Q4738898
    https://en.wikipedia.org/wiki/AmRest

    This spider is specifically for the common functionality across all child brands.
    """

    api_brand_key: str = None
    api_brand_country_key: str = None
    api_source: str = None
    api_auth_source: str = None
    api_channel: str = None
    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v1\/auth\/get-token$",
            headers=r'{"api_brand_key": .brand, "api_source": .source}',
            data=r'{"api_auth_source": .source}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v1\/auth\/get-token$",
            headers=r'{"api_brand_key": .brand}',
            data=r'{"api_auth_source": .source}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v1\/auth\/get-token$",
            headers=r'{"api_source": .source}',
            data=r'{"api_auth_source": .source}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v1\/auth\/get-token$",
            data=r'{"api_auth_source": .source}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v[23]\/restaurants\/$",
            headers=r'{"api_brand_key": .brand, "api_source": .source}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v[23]\/restaurants\/$",
            headers=r'{"api_brand_key": .brand}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v[23]\/restaurants\/$",
            headers=r'{"api_source": .source}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v[23]\/restaurants\/$",
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v2\/restaurants\/(?:\d+\/(?P<api_channel>[A-Z_]+)|details\/\d+)$",
            headers=r'{"api_brand_key": .brand, "api_source": .source}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v2\/restaurants\/(?:\d+\/(?P<api_channel>[A-Z_]+)|details\/\d+)$",
            headers=r'{"api_brand_key": .brand}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v2\/restaurants\/(?:\d+\/(?P<api_channel>[A-Z_]+)|details\/\d+)$",
            headers=r'{"api_source": .source}',
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/api\.amrest\.eu\/amdv\/ordering-api\/(?P<api_brand_country_key>[^\/]+)\/rest\/v2\/restaurants\/(?:\d+\/(?P<api_channel>[A-Z_]+)|details\/\d+)$",
        ),
    ]

    def start_requests(self):
        headers = {
            "Brand": self.api_brand_key,
        }
        if self.api_source:
            headers.update({"Source": self.api_source})
        data = {
            "deviceUuid": "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF",
            "deviceUuidSource": "FINGERPRINT",
            "source": f"{self.api_auth_source}",
        }
        yield JsonRequest(
            url=f"https://api.amrest.eu/amdv/ordering-api/{self.api_brand_country_key}/rest/v1/auth/get-token",
            headers=headers,
            data=data,
            callback=self.parse_auth_token,
        )

    def parse_auth_token(self, response):
        auth_token = response.json()["token"]
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Brand": self.api_brand_key,
        }
        if self.api_source:
            headers.update({"Source": self.api_source})
        yield JsonRequest(
            url=f"https://api.amrest.eu/amdv/ordering-api/{self.api_brand_country_key}/rest/v3/restaurants/",
            headers=headers,
            callback=self.parse_restaurants_list,
        )

    def parse_restaurants_list(self, response):
        headers = {
            "Authorization": response.request.headers.get("Authorization"),
            "Brand": self.api_brand_key,
        }
        if self.api_source:
            headers.update({"Source": self.api_source})
        for restaurant in response.json()["restaurants"]:
            restaurant_id = restaurant["id"]
            if self.api_channel:
                yield JsonRequest(
                    url=f"https://api.amrest.eu/amdv/ordering-api/{self.api_brand_country_key}/rest/v2/restaurants/{restaurant_id}/{self.api_channel}",
                    headers=headers,
                    callback=self.parse_restaurant_details,
                )
            else:
                yield JsonRequest(
                    url=f"https://api.amrest.eu/amdv/ordering-api/{self.api_brand_country_key}/rest/v2/restaurants/details/{restaurant_id}",
                    headers=headers,
                    callback=self.parse_restaurant_details,
                )

    def parse_restaurant_details(self, response):
        location = response.json()["details"]
        item = DictParser.parse(location)
        item["ref"] = str(location["id"])
        item["postcode"] = location["addressPostalCode"]
        item["housenumber"] = location.get("addressStreetNo")
        item["street"] = location["addressStreet"]
        item["opening_hours"] = self.parse_hours(location["facilityOpenHours"])

        apply_yes_no(Extras.DELIVERY, item, location.get("delivery"), False)
        apply_yes_no(Extras.TAKEAWAY, item, location.get("takeaway"), False)
        apply_yes_no(Extras.INDOOR_SEATING, item, location.get("dineIn"), False)
        extra_features = [feature["key"] for feature in location.get("filters", {})]
        if extra_features:
            apply_yes_no(Extras.DRIVE_THROUGH, item, "driveThru" in extra_features, False)
            apply_yes_no(Extras.OUTDOOR_SEATING, item, location.get("garden"), False)
            apply_yes_no(Extras.WIFI, item, "wifi" in extra_features, False)

        yield from self.post_process_item(item, response, location)

    def post_process_item(self, item: Feature, response: Response, location: dict):
        yield item

    @staticmethod
    def parse_hours(opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in [
            "openHoursMon",
            "openHoursTue",
            "openHoursWed",
            "openHoursThu",
            "openHoursFri",
            "openHoursSat",
            "openHoursSun",
        ]:
            for times in opening_hours[day]:
                oh.add_range(day[-3:], times["openFrom"], times["openTo"])
        return oh
