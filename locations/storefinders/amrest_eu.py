from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AmrestEUSpider(Spider):
    """
    AmRest is a European multinational casual dining, fast-food restaurant and coffee shop operator headquartered in the Spanish capital, Madrid
    https://www.wikidata.org/wiki/Q4738898
    https://en.wikipedia.org/wiki/AmRest

    This spider is specifically for the common functionality across all child brands.
    """

    base_urls = ["https://api.amrest.eu/amdv/ordering-api/{}/"]
    auth_url = "rest/v1/auth/get-token"
    restaurants_url = "rest/v2/restaurants/"
    base_headers = {"source": "WEB"}
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
        for root_url in self.base_urls:
            yield JsonRequest(
                url=(root_url + self.auth_url),
                data=self.auth_data,
                headers=self.base_headers,
                callback=self.fetch_restaurants,
                meta={"root_url": root_url},
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

    def parse_item(self, item, feature, **kwargs):
        yield item

    def parse_hours(self, opening_hours) -> OpeningHours:
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
