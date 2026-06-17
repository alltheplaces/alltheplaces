import json
from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class GoOutdoorsGBSpider(Spider):
    name = "go_outdoors_gb"
    item_attributes = {"brand": "Go Outdoors", "brand_wikidata": "Q75293941"}
    start_urls = ["https://www.gooutdoors.co.uk/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//*[@id="app-store-locator"]//script[@type="application/json"]/text()').get()
        )["stores"]:
            yield JsonRequest(
                url=f"https://extensions.gooutdoors.co.uk/api/stores/{location['id']}", callback=self.parse_details
            )

    def parse_details(self, response: Response):
        data = response.json().get("store")
        if not data:
            print("Error parsing: {}".format(response.url))
            return
        item = DictParser.parse(data)
        item["branch"] = item.pop("name").replace("GO Outdoors ", "")
        item["state"] = data["big_region"]
        item["phone"] = data["local_phone"]
        item["street_address"] = merge_address_lines([data["address_2"], data["address_1"]])
        oh = OpeningHours()
        for day, time in data.get("hours_sets", "").get("primary", "").get("days").items():
            for open_close_time in time:
                open_time = open_close_time["open"]
                close_time = open_close_time["close"]
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_OUTDOOR, item)

        yield item
