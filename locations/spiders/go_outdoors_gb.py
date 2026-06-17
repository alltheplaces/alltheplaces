import json
from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
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

    def parse_details(self, response: Response, **kwargs: Any) -> Any:
        data = response.json().get("store")
        if data:
            item = DictParser.parse(data)
            item["state"] = data["big_region"]
            item["phone"] = data["local_phone"]
            item["street_address"] = merge_address_lines([data["address_1"], data["address_2"]])
            if image := data["photo_1"]:
                item["image"] = image.split(",", 1)[0]

            item["opening_hours"] = OpeningHours()
            for day, rules in data.get("hours_sets", "").get("primary", "").get("days").items():
                for rule in rules:
                    item["opening_hours"].add_range(day, rule["open"], rule["close"])

            if item["name"].startswith("GO Outdoors Express "):
                item["branch"] = item.pop("name").removeprefix("GO Outdoors Express ")
                item["name"] = "Go Outdoors Express"
            else:
                item["branch"] = item.pop("name").removeprefix("GO Outdoors ")
                item["name"] = "Go Outdoors"

            apply_category(Categories.SHOP_OUTDOOR, item)

            yield item
