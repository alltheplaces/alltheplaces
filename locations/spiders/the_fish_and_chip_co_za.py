from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class TheFishAndChipCoZASpider(Spider):
    name = "the_fish_and_chip_co_za"
    item_attributes = {"brand": "The Fish & Chip Co", "brand_wikidata": "Q126916268"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://admin.goreview.co.za/website/api/locations/search",
            data={
                "domain": "fishchipco.localpages.io",
                "latitude": "null",
                "longitude": "null",
                "attributes": "false",
                "radius": "null",
                "initialLoad": "true",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("The Fish & Chip Co ")
            item["website"] = location["local_page_url"]

            yield item
