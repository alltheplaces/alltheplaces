from datetime import datetime
from typing import Any, AsyncIterator, Iterable

import chompjs
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksHKMOSpider(JSONBlobSpider):
    name = "starbucks_hk_mo"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    requires_proxy = "HK"

    def make_request(self, page: int, limit: int = 100) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.starbucks.com.hk/en/find-a-store?page={page}&limit={limit}",
            cb_kwargs=dict(page=page, limit=limit),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def extract_json(self, response: TextResponse) -> list[dict]:
        scripts = response.xpath(
            "//script[starts-with(text(), 'self.__next_f.push')][contains(text(), 'items')]/text()"
        ).getall()
        data = dict(parse_rsc("".join([s for n, s in [chompjs.parse_js_object(s) for s in scripts]]).encode()))
        return DictParser.get_nested_key(data, "items")

    def parse(self, response: TextResponse, page: int, limit: int) -> Any:
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features) or []
        if len(features) == limit:
            yield self.make_request(page + 1)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["MasterStoreID"]
        item["branch"] = item.pop("name")
        item["extras"]["branch:en"] = feature["CommonStoreName"]
        item["extras"]["branch:zh"] = feature["CommonStoreNameTH"]
        item["street_address"] = feature["Sub_District"]
        item["city"] = feature["District"]
        item["phone"] = feature.get("Mobile")

        apply_category(Categories.COFFEE_SHOP, item)

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            key = day.lower()
            open_time = feature.get(f"{key}OpeningTime", "")
            close_time = feature.get(f"{key}ClosingTime", "")
            if open_time and close_time:
                open_time = datetime.strptime(open_time, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M")
                close_time = (
                    datetime.strptime(close_time, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M").replace("00:00", "23:59")
                )

                item["opening_hours"].add_range(day, open_time, close_time)

        yield item
