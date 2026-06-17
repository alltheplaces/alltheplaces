import json
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class MilletsGBSpider(Spider):
    name = "millets_gb"
    item_attributes = {"brand": "Millets", "brand_wikidata": "Q64822903"}
    start_urls = ["https://www.millets.co.uk/pages/our-stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store_id in json.loads(
            response.xpath('//*[@id="app-store-locator"]//*[@type="application/json"]//text()').get()
        )["stores"]:
            yield JsonRequest(
                url=f"https://integrations-c3f9339ff060a907cbd8.o2.myshopify.dev/api/stores?fid={store_id['id']}",
                callback=self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        for raw_data in response.json()["stores"]:
            item = DictParser.parse(raw_data)
            item["street_address"] = merge_address_lines([raw_data["address_1"], raw_data["address_2"]])
            item["phone"] = raw_data.get("local_phone")
            item["website"] = "https://www.millets.co.uk/pages/stores/" + item["name"].lower().replace(
                " ", "-"
            ).replace("\xa0", "-")
            item["branch"] = item.pop("name").removeprefix("Millets").strip()

            try:
                item["opening_hours"] = self.parse_hours(raw_data["hours_sets"]["primary"]["days"])
            except:
                pass

            apply_category(Categories.SHOP_OUTDOOR, item)

            yield item

    def parse_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, times in rules.items():
            for rule in times:
                oh.add_range(day, rule["open"], rule["close"])
        return oh
