import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class KfcAmrestSpider(scrapy.Spider):
    name = "kfc_amrest"
    item_attributes = {"brand": "KFC", "brand_wikidata": "Q524757"}
    start_urls = [
        "https://api.amrest.eu/amdv/ordering-api/KFC_PL",  # https://kfc.pl/en/restaurants
        "https://api.amrest.eu/amdv/ordering-api/KFC_HU",  # https://kfc.hu/en/restaurants
        "https://api.amrest.eu/amdv/ordering-api/KFC_CZ",  # https://kfc.cz/en/restaurants
        "https://api.amrest.eu/amdv/ordering-api/KFC_HR",  # https://kfc.hr/en/restaurants
        "https://api.amrest.eu/amdv/ordering-api/KFC_RS",  # https://kfc.rs/en/restaurants
    ]
    allowed_domains = ["api.amrest.eu"]

    def start_requests(self):
        for root_url in self.start_urls:
            kfc_country = root_url.split("/")[-1].split("_")[-1].lower()
            yield scrapy.http.JsonRequest(
                root_url + "/rest/v1/auth/get-token",
                data={
                    # data is sent like this by JS at kfc.pl
                    # no actual fingerprinting is done
                    "deviceUuidSource": "FINGERPRINT",
                    "deviceUuid": "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF",
                    "source": "WEB_KFC",
                },
                meta={"root_url": root_url, "country": kfc_country},
                callback=self.fetch_locations,
            )

    def fetch_locations(self, response):
        yield self.request(
            response.meta["root_url"] + "/rest/v2/restaurants/", response.json()["token"], response.meta["country"]
        )

    def request(self, url, access_token, country):
        return scrapy.Request(url, headers={"Authorization": f"Bearer {access_token}"}, meta={"country": country})

    def parse(self, response):
        data = response.json()

        for location in data["restaurants"]:
            item = DictParser.parse(location)
            item.pop("street_address")
            item["country"] = response.meta["country"]
            item["street"] = location["addressStreet"]
            item["opening_hours"] = OpeningHours()
            if location["openHours"][0]["open24h"]:
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            else:
                item["opening_hours"].add_days_range(
                    DAYS, location["openHours"][0]["openFrom"], location["openHours"][0]["openTo"]
                )

            available_keys = [filter["key"] for filter in location["filters"] if filter["available"]]
            apply_yes_no(Extras.DRIVE_THROUGH, item, "driveThru" in available_keys)
            apply_yes_no(Extras.WIFI, item, "wifi" in available_keys)
            yield item
