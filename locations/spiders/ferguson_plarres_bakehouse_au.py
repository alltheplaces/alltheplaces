import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FergusonPlarresBakehouseAUSpider(Spider):
    name = "ferguson_plarres_bakehouse_au"
    item_attributes = {"brand": "Ferguson Plarre's Bakehouse", "brand_wikidata": "Q5444249"}
    allowed_domains = ["www.fergusonplarre.com.au"]
    start_urls = ["https://www.fergusonplarre.com.au/rest/e/get/locations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        query = {"sort": [{"position": {"order": "asc"}}], "size": 100, "query": {"term": {"status": 1}}}
        for url in self.start_urls:
            yield JsonRequest(url=url, data=query, method="POST")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["hits"]:
            item = DictParser.parse(location["_source"])
            item["branch"] = item.pop("name").removesuffix(" Bakery")
            item["addr_full"] = re.sub(r"\s*-\s*This store is located on.*", "", item["addr_full"])
            item["website"] = "https://www.fergusonplarre.com.au/" + location["_source"]["url_key"]
            item["opening_hours"] = self.parse_opening_hours(location["_source"]["schedule"])
            yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day_name, day in rules.items():
            if not day["status"]:
                continue
            opening_hours.add_range(day_name, day["from"], day["to"])
        return opening_hours
