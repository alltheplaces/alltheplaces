import re

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class HealthhubSGSpider(Spider):
    name = "healthhub_sg"
    start_urls = [
        "https://eservices.healthhub.sg/public/directory",
    ]

    def parse(self, response, **kwargs):
        url_for_api_key = response.xpath("//script[@type='module']/@src").get()
        if url_for_api_key:
            url_for_api_key = f"https://eservices.healthhub.sg{url_for_api_key}"
            yield Request(url_for_api_key, callback=self.parse_api_key)

    def parse_api_key(self, response, **kwargs):
        api_key = re.search(r"VITE_REACT_GREEN_APP_API_KEY:\s*\"(.+)\",VITE_REACT_GREEN", response.text).group(1)
        if api_key:
            yield self.make_request(1, api_key)

    def make_request(self, page: int, key: str) -> JsonRequest:
        return JsonRequest(
            url="https://api.hcc.healthhub.sg/active/v1/public/directory/locations",
            data={"Filter": [58, 56], "PageNumber": page, "Language": "en"},
            method="POST",
            callback=self.parse_locations,
            headers={"x-api-key": key},
            cb_kwargs={"key": key},
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json().get("Result", []).get("Locations", []):
            yield JsonRequest(
                url="https://api.hcc.healthhub.sg/active/v1/public/directory/locationdetails",
                data={"DirectoryLocationId": location.get("DirectoryLocationId"), "Language": "en"},
                method="POST",
                callback=self.parse_details,
                headers={"x-api-key": kwargs["key"]},
            )
        if response.json().get("Result").get("CurrentPageNumber") <= response.json().get("Result").get("TotalPages"):
            yield self.make_request(response.json().get("Result").get("CurrentPageNumber") + 1, kwargs["key"])

    def parse_details(self, response):
        data = response.json().get("Result", []).get("LocationDetails", [])
        data.pop("NearestLocations")
        item = DictParser.parse(data)
        item["ref"] = data.get("DirectoryLocationId")
        item["postcode"] = str(item["postcode"])
        if item.get("website"):
            item["website"] = ["https://" + item["website"] if "https://" not in item["website"] else item["website"]]
        oh = OpeningHours()
        oh.add_ranges_from_string(data.get("OperatingHour", ""))
        item["opening_hours"] = oh
        apply_category(Categories.HOSPITAL, item)
        yield item
