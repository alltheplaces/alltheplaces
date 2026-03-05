import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TacoBuenoSpider(Spider):
    name = "taco_bueno"
    item_attributes = {"brand": "Taco Bueno", "brand_wikidata": "Q7673958"}
    start_urls = ["https://locations.tacobueno.com/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        build_id = re.search(r"buildId\"\s*:\s*\"(.+)\",", response.text).group(1)
        yield JsonRequest(
            url=f"https://locations.tacobueno.com/_next/data/{build_id}/index.json", callback=self.parse_locations
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json()["pageProps"]["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["storeCode"]
            item["street_address"] = ", ".join(location["addressLines"])
            item["website"] = item["website"].replace("\t", "")
            oh = OpeningHours()
            oh.add_ranges_from_string(",".join(location["formattedBusinessHours"]))
            item["opening_hours"] = oh
            yield item
