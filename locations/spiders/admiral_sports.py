import json
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AdmiralSportsSpider(JSONBlobSpider):
    name = "admiral_sports"
    item_attributes = {"brand": "Admiral Sports", "brand_wikidata": "Q4683720"}
    locations_key = ["data", "mc_asl_list", "items"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://payment.admiralsports.shop/graphql",
            data={
                "query": """{
                mc_asl_list {
                    items {
                        id
                        lat
                        lng
                        branch: name
                        street_address: address
                        zip
                        city
                        state
                        country
                        schedule_string
                        phone
                        actions_serialized
                        slug: url_key
                    }
                }
            }"""
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["branch"]
        if schedule_string := feature.get("schedule_string"):
            item["opening_hours"] = OpeningHours()
            for day, hours in json.loads(schedule_string).items():
                from_time = f"{hours['from']['hours']}:{hours['from']['minutes']}"
                to_time = f"{hours['to']['hours']}:{hours['to']['minutes']}"
                item["opening_hours"].add_range(day, from_time, to_time)
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
