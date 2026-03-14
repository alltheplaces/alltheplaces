from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class SydneyToolsAUSpider(Spider):
    name = "sydney_tools_au"
    item_attributes = {"brand": "Sydney Tools", "brand_wikidata": "Q116779309"}
    allowed_domains = ["sydneytools.com.au"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        graphql_query = "query routes_StoreList_Query { viewer { ...StoreList_viewer id } } fragment StoreList_viewer on Customer { id email myStore { id } stores(first: 10000) { edges { node { id name address city postcode state description fax phone lat lng canPickup hours { monday { open close } tuesday { open close } wednesday { open close } thursday { open close } friday { open close } saturday { open close } sunday { open close } } } } } }"
        data = {"query": graphql_query, "variables": {}}
        yield JsonRequest(url="https://sydneytools.com.au/graphql", data=data)

    def parse(self, response):
        stores = response.json()["data"]["viewer"]["stores"]["edges"]
        for store in stores:
            item = DictParser.parse(store["node"])
            item["street_address"] = item.pop("addr_full")
            item["website"] = (
                "https://sydneytools.com.au/stores/"
                + item["state"].lower()
                + "/"
                + item["name"].lower().replace(" ", "-")
            )
            oh = OpeningHours()
            for day_name, day_hours in store["node"]["hours"].items():
                oh.add_range(DAYS_EN[day_name.title()], day_hours["open"], day_hours["close"], "%H:%M")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
