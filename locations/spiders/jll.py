import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class JllSpider(Spider):
    name = "jll"
    item_attributes = {"brand": "JLL", "brand_wikidata": "Q1703389"}
    start_urls = ["https://www.jll.com/en-in/locations?sort_by_relevance=relevance&location_page=1"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        key_match = re.search(r"subscriptionIdentifier:\s*\"(.*)\",", response.text)
        if not key_match:
            self.logger.error("Could not find subscription key in response")
            return
        key = key_match.group(1)
        yield JsonRequest(
            url="https://www.jll.com/api/search/template",
            headers={"subscription-key": key.strip()},
            data={
                "id": "jll_location_search_template_v3",
                "params": {"size": 500, "from": 0, "countries": ["United States"], "language": "en-US"},
            },
            method="POST",
            callback=self.parse_location,
        )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["hits"]["hits"]:
            location.update(location.pop("_source"))
            item = DictParser.parse(location)
            item["ref"] = location["_id"]
            yield item
