from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class AmrestEUSpider(Spider):
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

    # following 'deviceUuid' is the default for BK and KFC. PH uses generated one, but seems to work
    # with default one as well
    auth_data = {
        "deviceUuid": "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF",
        "deviceUuidSource": "FINGERPRINT",
        "source": "WEB_KFC",
    }

    CHANNELS = {
        "takeout": "TAKEOUT",
        "takeaway": "TAKEAWAY",
        "dineIn": "DINE_IN",
        "delivery": "DELIVERY",
    }

    # Restaurants details endpoint url is different for different brands - for PH and BK involves channel.
    # Usually it works out with TAKEOUT, but if it's not supported by restaurant, different channel was
    # noticed to work fine.
    def make_details_url(self, root_url, restaurant):
        match self.item_attributes["brand"]:
            case "KFC":
                return f"{root_url}{self.restaurants_url}details/{restaurant['id']}"
            case "Pizza Hut" | "Burger King" | "La Tagliatella":
                for channel_key, channel in self.CHANNELS.items():
                    if restaurant.get(channel_key):
                        return f"{root_url}{self.restaurants_url}{restaurant['id']}/{channel}"
            case _:
                raise CloseSpider(f"Brand '{self.item_attributes['brand']}' not supported")

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

    def fetch_restaurants(self, response):
        root_url = response.meta["root_url"]
        token = response.json()["token"]
        yield JsonRequest(
            url=(root_url + self.restaurants_url),
            headers=self.base_headers | {"authorization": f"Bearer {token}"},
            callback=self.fetch_details,
            meta={"root_url": root_url, "token": token},
        )

    def fetch_details(self, response):
        for restaurant in response.json()["restaurants"]:
            yield JsonRequest(
                url=self.make_details_url(response.meta["root_url"], restaurant),
                headers=self.base_headers | {"authorization": f'Bearer {response.meta["token"]}'},
            )

    def parse(self, response):
        feature = response.json()["details"]

        item = DictParser.parse(feature)

        item["postcode"] = feature["addressPostalCode"]
        item["housenumber"] = feature.get("addressStreetNo")
        item["street"] = feature["addressStreet"]
        item["opening_hours"] = self.parse_hours(feature["facilityOpenHours"])

        apply_yes_no(Extras.DRIVE_THROUGH, item, feature.get("driveThru"))
        apply_yes_no(Extras.DELIVERY, item, feature.get("delivery"))
        apply_yes_no(Extras.TAKEAWAY, item, feature.get("takeaway"))

        yield from self.parse_item(item, feature)

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

        yield from self.parse_item(item, location)

    def parse_item(self, item: Feature, location: dict):
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
