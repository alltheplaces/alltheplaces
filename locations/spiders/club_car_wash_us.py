from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class ClubCarWashUSSpider(Spider):
    name = "club_car_wash_us"
    item_attributes = {"brand": "Club Car Wash", "brand_wikidata": "Q122850169"}
    start_urls = [
        "https://clubcarwash.com/wp-json/wpgmza/v1/marker-listing/base64eJyrVirIKHDOSSwuVrJSCg9w941yjInxTSzKTi3yySwuycxLj4lxSizOTA5JTMpJVdJRKi5JLCpRsjLQUcpJzUsvyVCy0jXUUcpNLIjPTAEaYaRUCwCwfxth"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["meta"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = location["link"]
            item["image"] = location["pic"]

            yield item
