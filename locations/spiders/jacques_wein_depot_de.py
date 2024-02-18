from scrapy import Request, Spider
from scrapy.http import JsonRequest
from unidecode import unidecode

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class JacquesWeinDepotDESpider(Spider):
    name = "jacques_wein_depot_de"
    item_attributes = {
        "brand": "Jacques’ Wein-Depot",
        "brand_wikidata": "Q1678150",
        "extras": Categories.SHOP_WINE.value,
    }
    allowed_domains = ["www.jacques.de", "commerce.api.jacques.de"]
    start_urls = ["https://www.jacques.de/weindepots"]

    def parse(self, response):
        main_js_url = "https://www.jacques.de/" + response.xpath('//script[contains(@src, "main.")]/@src').get()
        yield Request(url=main_js_url, callback=self.parse_api_key)

    def parse_api_key(self, response):
        api_key = response.text.split('xApiKeyCommerce:"', 1)[1].split('"', 1)[0]
        yield JsonRequest(
            url="https://commerce.api.jacques.de/authentication/v1/anonymous",
            method="POST",
            headers={"x-api-key": api_key},
            callback=self.parse_auth_token,
        )

    def parse_auth_token(self, response):
        api_key = response.request.headers.get("x-api-key")
        auth_token = response.json()["token"]
        headers = {
            "Accept-Language": "de-DE",
            "x-api-key": api_key,
            "Authorization": f"Bearer {auth_token}",
        }
        yield JsonRequest(
            url="https://commerce.api.jacques.de/depot/v1/locations",
            headers=headers,
            callback=self.parse_locations_list,
        )

    def parse_locations_list(self, response):
        api_key = response.request.headers.get("x-api-key")
        auth_header_value = response.request.headers.get("Authorization")
        headers = {
            "Accept-Language": "de-DE",
            "x-api-key": api_key,
            "Authorization": auth_header_value,
        }
        for location in response.json():
            location_id = location["identifier"]
            yield JsonRequest(
                url=f"https://commerce.api.jacques.de/depot/v1/depot/{location_id}",
                headers=headers,
                callback=self.parse_location,
            )

    def parse_location(self, response):
        location = response.json()
        item = DictParser.parse(location)
        item["lat"] = location["location"]["coordinates"][0]
        item["lon"] = location["location"]["coordinates"][1]
        item["phone"] = location["address"].get("phone")
        item["email"] = location["address"].get("email")
        item["website"] = "https://www.jacques.de/weindepot/{}/{}".format(
            item["ref"], unidecode(item["name"]).replace(" ", "-")
        )

        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in location.get("openingHours").items():
            if not isinstance(day_hours, dict):
                # Ignore validFrom and validTo fields that occasionally appear
                continue
            if "postMeridiem" in day_hours.keys():
                item["opening_hours"].add_range(
                    day_name.title(), day_hours["postMeridiem"]["from"], day_hours["postMeridiem"]["to"], "%H%M"
                )
            elif "anteMeridiem" in day_hours.keys():
                item["opening_hours"].add_range(
                    day_name.title(), day_hours["anteMeridiem"]["from"], day_hours["anteMeridiem"]["to"], "%H%M"
                )

        yield item
