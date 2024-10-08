import re

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class PncBankUSSpider(Spider):
    name = "pnc_bank_us"
    item_attributes = {"brand": "PNC Bank", "brand_wikidata": "Q38928"}
    start_urls = ["https://apps.pnc.com/locator/bundle/bundle.js"]
    allowed_domains = ["apps.pnc.com"]

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_app_key)

    def parse_app_key(self, response):
        app_key = response.text.split('xAppKey=o?"', 1)[1].split('"', 1)[0]
        yield JsonRequest(
            url="https://apps.pnc.com/dsa-api/v1/auth/getToken",
            method="POST",
            headers={"X-App-Key": app_key},
            callback=self.parse_jwt,
        )

    def parse_jwt(self, response):
        jwt = response.headers["pnc_api_key"].decode("utf-8")
        headers = {"Authorization": f"Bearer {jwt}", "X-App-Key": response.request.headers["X-App-Key"].decode("utf-8")}
        yield JsonRequest(
            url="https://apps.pnc.com/locator-api/locator/api/v1/locator/browse",
            headers=headers,
            callback=self.parse_cities_list,
        )

    def parse_cities_list(self, response):
        headers = {
            "Authorization": response.request.headers["Authorization"].decode("utf-8"),
            "X-App-Key": response.request.headers["X-App-Key"].decode("utf-8"),
        }
        for state_code, cities_list in response.json().items():
            for city_locations_list in cities_list["locations"]:
                for location in city_locations_list["locationDetails"]:
                    location_external_id = location["externalId"]
                    yield JsonRequest(
                        url=f"https://apps.pnc.com/locator-api/locator/api/v2/location/details/{location_external_id}",
                        headers=headers,
                        callback=self.parse_location,
                    )

    def parse_location(self, response):
        location = response.json()
        item = DictParser.parse(location)
        item["ref"] = location.get("externalId")
        item["lat"] = location["address"].get("latitude")
        item["lon"] = location["address"].get("longitude")
        item["street_address"] = clean_address(
            [location["address"].get("address1"), location["address"].get("address2")]
        )
        item["website"] = "https://apps.pnc.com/locator/result-details/{}/{}".format(
            item["ref"], re.sub(r"[\s\-]+", "-", item["name"].lower())
        )

        for contact_info in location["contactInfo"]:
            if contact_info["contactType"] == "External Phone":
                item["phone"] = contact_info["contactInfo"]

        if location["locationType"].get("locationTypeDesc") == "BRANCH":
            apply_category(Categories.BANK, item)
        else:
            self.logger.error("Unknown location type: {}".format(location["locationType"].get("locationTypeDesc")))

        services = [service["service"]["serviceName"] for service in location["services"]]
        apply_yes_no(Extras.ATM, item, "ATM" in services, False)
        apply_yes_no(Extras.WIFI, item, "WiFi Available" in services, False)
        apply_yes_no(Extras.WHEELCHAIR, item, "Handicapped Access" in services, False)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru Hours" in services, False)

        if "Lobby Hours" in services:
            item["opening_hours"] = OpeningHours()
            for service in location["services"]:
                if service["service"]["serviceName"] == "Lobby Hours":
                    if service["hours"]["twentyFourHours"]:
                        item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
                        break
                    for day_name, day_hours in service["hours"].items():
                        if day_name.title() in DAYS_FULL:
                            for hours_range in day_hours:
                                if not hours_range["open"] or not hours_range["close"]:
                                    continue
                                item["opening_hours"].add_range(
                                    day_name.title(), hours_range["open"], hours_range["close"], "%I:%M %p"
                                )

        yield item
