import re

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HealthhubSGSpider(Spider):
    name = "healthhub_sg"
    start_urls = [
        "https://eservices.healthhub.sg/healthhubng/public/services/directory/56",
        "https://eservices.healthhub.sg/healthhubng/public/services/directory/58",
    ]

    def parse(self, response, **kwargs):
        url_for_api_key = response.xpath("//script[@type='module']/@src").get()
        if url_for_api_key:
            url_for_api_key = f"https://eservices.healthhub.sg{url_for_api_key}"
            yield Request(url_for_api_key, callback=self.parse_api_key)

    def parse_api_key(self, response, **kwargs):
        for m in re.findall(r'''VITE_REACT_APP_API_KEY:\s*"([^"\s\n]+)"''', response.text):
            api_key = m

        if api_key:
            locations_urls = [
                "https://api.healthhub.sg/healthhub/prod/v2/Directory/LocationList?pageNum=1&pageSize=100&categoryId=56",
                "https://api.healthhub.sg/healthhub/prod/v2/Directory/LocationList?pageNum=1&pageSize=100&categoryId=58",
            ]
            for url in locations_urls:
                yield Request(url, callback=self.parse_locations, headers={"X-Api-Key": api_key})

    def parse_locations(self, response, **kwargs):
        for location in response.json().get("Results", []):
            item = DictParser.parse(location)
            if location.get("Open24H") == "Y":
                item["opening_hours"] = "Mo-Su 00:00-24:00"

            apply_category(Categories.HOSPITAL, item)

            yield item
