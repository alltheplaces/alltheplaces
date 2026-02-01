from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.structured_data_spider import clean_facebook, clean_instagram, clean_twitter


class RayWhiteAUNZSpider(Spider):
    name = "ray_white_au_nz"
    item_attributes = {"brand": "Ray White", "brand_wikidata": "Q81077729"}
    allowed_domains = ["raywhiteapi.ep.dynamics.net"]
    start_urls = ["https://raywhiteapi.ep.dynamics.net/v1/organisations?apiKey=6625c417-067a-4a8e-8c1d-85c812d0fb25"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        data = {
            "from": 0,
            "size": 10000,
            "public": True,
            "sort": [
                {
                    "field": "location",
                    "lat": -23.12,
                    "lon": 132.13,
                    "order": "asc",
                }
            ],
            "exists": {
                "AND": [
                    "emailAddress",
                    "webSite",
                ]
            },
            "countryCode": [
                "AU",
                "NZ",
            ],
            "subType": [
                "Rural",
                "Residential",
            ],
            "location": {
                "lat": -23.12,
                "lon": 132.13,
                "distance": "100000km",
            },
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, data=data, method="POST")

    def parse(self, response):
        for location in response.json()["data"]:
            if location["value"]["status"] != "Active":
                continue
            item = DictParser.parse(location["value"])
            item["lat"] = location["value"]["address"]["location"]["lat"]
            item["lon"] = location["value"]["address"]["location"]["lon"]
            item["website"] = location["value"]["webSite"]
            for phone_number in location["value"].get("phones", []):
                if phone_number["typeCode"] == "FIX":  # Fixed phone number
                    item["phone"] = phone_number["internationalizedNumber"]
                    break
            if location["value"].get("profile"):
                for social_account in location["value"]["profile"].get("socialLinks", []):
                    if social_account["type"] == "Facebook":
                        item["facebook"] = clean_facebook(social_account["link"])
                    elif social_account["type"] == "Instagram":
                        item["extras"]["contact:instagram"] = clean_instagram(social_account["link"])
                    elif social_account["type"] == "Twitter":
                        item["twitter"] = clean_twitter(social_account["link"])
                for photo in location["value"]["profile"].get("photos", []):
                    if photo["typeCode"] == "OPEXT":  # Exterior photo
                        item["image"] = photo["fileName"]
                        break
            yield item
