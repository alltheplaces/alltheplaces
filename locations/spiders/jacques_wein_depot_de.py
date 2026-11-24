import re

from scrapy import Request, Spider
from scrapy.http import JsonRequest
from unidecode import unidecode

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class JacquesWeinDepotDESpider(Spider):
    name = "jacques_wein_depot_de"
    item_attributes = {"brand": "Jacques' Wein-Depot", "brand_wikidata": "Q1678150"}
    allowed_domains = ["www.jacques.de", "commerce.api.jacques.de"]
    start_urls = ["https://www.jacques.de/weindepots"]

    def parse(self, response):
        main_js_url = response.urljoin(response.xpath('//script[starts-with(@src, "main")]/@src').get())
        yield Request(url=main_js_url, callback=self.parse_main_js)

    def parse_main_js(self, response):
        if 'xApiKeyCommerce:"' in response.text:
            yield from self.parse_api_key(response)
            return
        # The API key is usually defined in one of the chunks that main.js imports.
        for chunk in sorted(set(re.findall(r'from"\./(chunk-\w+\.js)"', response.text))):
            yield Request(url=response.urljoin(chunk), callback=self.parse_chunk_js)

    def parse_chunk_js(self, response):
        if 'xApiKeyCommerce:"' in response.text:
            yield from self.parse_api_key(response)

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
            day_is_open = False
            for period in ("anteMeridiem", "postMeridiem"):
                if period not in day_hours:
                    continue
                # A period from 0000 to 0000 is a placeholder for no opening time.
                if day_hours[period]["from"] == day_hours[period]["to"] == "0000":
                    continue
                item["opening_hours"].add_range(
                    day_name.title(), day_hours[period]["from"], day_hours[period]["to"], "%H%M"
                )
                day_is_open = True
            if not day_is_open:
                item["opening_hours"].set_closed(day_name.title())

        apply_category(Categories.SHOP_WINE, item)

        yield item
