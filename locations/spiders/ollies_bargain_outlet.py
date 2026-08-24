import json
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class OlliesBargainOutletSpider(Spider):
    name = "ollies_bargain_outlet"
    allowed_domains = ["wswrapper.bullseyelocations.com", "ws.bullseyelocations.com"]
    item_attributes = {"brand": "Ollie's Bargain Outlet", "brand_wikidata": "Q7088304"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 45}
    requires_proxy = "US"
    start_urls = [
        "https://wswrapper.bullseyelocations.com/InterfaceConfiguration/GetInterfaceConfiguration?interfaceName=ollies-bargain-outlet-near-me&languageCode=en&version="
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        api_key = response.json().get("apiKey")
        yield JsonRequest(
            url=f"https://ws.bullseyelocations.com/RestSearch.svc/GetLocationList?countryIds=1&action=json&ClientId=8902&ApiKey={api_key}",
            callback=self.parse_location,
        )

    def parse_location(self, response: Response):
        for location in (json.loads(response.json())).get("locations"):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            yield item
