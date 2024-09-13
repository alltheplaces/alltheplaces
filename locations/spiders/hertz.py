from datetime import datetime
from typing import Iterable

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


# TODO: Hertz also owns Dollar and Thrifty (https://en.wikipedia.org/wiki/Hertz_Global_Holdings
#       check if below spider can be re-used for those brands.
class HertzSpider(Spider):
    name = "hertz"
    item_attributes = {"brand": "Hertz", "brand_wikidata": "Q1543874"}
    custom_settings = {"CONCURRENT_REQUESTS": 1}  # Let's be more gentle with the API
    token = None
    user_agent = BROWSER_DEFAULT
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "user-agent": BROWSER_DEFAULT,
            "accept": "*/*",
            "accept-language": "en-US",
            "origin": "https://www.hertz.com",
            "referer": "https://www.hertz.com/",
        }
    }

    def start_requests(self):
        url = "https://api.hertz.io/api/login/token"
        headers = {
            "authorization": "Basic NjM5U0pXeTVUM2xJOXdpeHdVOUE3Q1JRUXpzQVpsT0RqclJ6dDdQeU1FRTpfYUR4UlA3ZVFORGNHLWt5LWY1MDhHSjlaQVdvRHoyMll2YjNqREZKZ2lv",
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        }

        formdata = {
            "grant_type": "client_credentials",
        }
        yield FormRequest(url, headers=headers, formdata=formdata, callback=self.parse_token)

    def parse_token(self, response: Response):
        self.token = response.json().get("access_token")
        yield from self.get_locations_page(url="https://api.hertz.io/v1/locations/HERTZ?_page=1&_size=1000")

    def get_locations_page(self, url: str):
        yield Request(
            url,
            headers={
                "authorization": f"Bearer {self.token}",
                "correlation-id": "2eb91a71-31da-48e7-901d-a9437a9b3975",
            },
            callback=self.parse,
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        response = response.json()
        for poi in response["data"]:
            poi = poi["data"]
            item = DictParser.parse(poi)
            item["ref"] = poi.get("oag")
            item["branch"] = item.pop("name")
            item["country"] = poi.get("countryCode")
            item["street_address"] = poi.get("address2")
            item["extras"]["check_date"] = (
                datetime.strptime(poi.get("lastUpdated"), "%a %b %d %H:%M:%S UTC %Y").strftime("%Y-%m-%d")
                if poi.get("lastUpdated")
                else None
            )
            item["extras"]["fax"] = poi.get("fax")
            item["website"] = (
                (
                    "https://www.hertz.com/rentacar/location/"
                    + (poi["country"] + "/" if poi["country"] else "")
                    + (item["state"] + "/" if item["state"] else "")
                    + (item["city"] + "/" if item["city"] else "")
                    + (item["ref"] if item["ref"] else "")
                )
                .lower()
                .replace(" ", "")
            )
            item["extras"]["type"] = poi.get("type")

            oh = OpeningHours()
            for day, day_hours in poi.get("openHours", {}).items():
                day = DAYS_EN.get(day.title())
                if not day_hours:
                    oh.set_closed(day)
                    continue
                for hours in day_hours:
                    oh.add_range(day, hours["start"], hours["end"])
            item["opening_hours"] = oh

            apply_category(Categories.CAR_RENTAL, item)
            yield item

        if next_page := response["_links"].get("next", {}).get("href"):
            yield from self.get_locations_page(next_page)
