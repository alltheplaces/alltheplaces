from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc


class PizzaWorldUSSpider(JSONBlobSpider):
    name = "pizza_world_us"
    item_attributes = {"brand": "Pizza World", "name": "Pizza World"}
    start_urls = ["https://pizzaworldonline.com/locations"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        scripts = response.xpath(
            "//script[starts-with(text(), 'self.__next_f.push')][contains(text(), 'SearchAction')]/text()"
        ).getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        return DictParser.get_nested_key(dict(parse_rsc("".join([s for n, s in objs]).encode())), "locations")

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address", {}))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("status") in ["temporarily-closed", "coming-soon"]:
            return
        item["ref"] = feature["storeNumber"]
        item.pop("name", None)
        item["branch"] = feature["publicDisplayName"].removeprefix("Pizza World — ")
        if phone := feature.get("publicPhone"):
            item["phone"] = phone
        item["website"] = f'https://pizzaworldonline.com/locations/{feature["slug"].strip("/")}'

        weekly_hours = feature.get("weeklyHours") or {}
        item["opening_hours"] = self.parse_opening_hours(weekly_hours)

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "pizza"

        yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, hours in rules.items():
            if hours.get("closed") is True:
                opening_hours.set_closed(day)
                continue
            for start, end in [("openTime", "closeTime"), ("secondOpenTime", "secondCloseTime")]:
                if hours.get(start):
                    opening_hours.add_ranges_from_string(f"{day}: {hours[start]} - {hours[end]}")
        return opening_hours
