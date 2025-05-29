import json
from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChestersTHSpider(JSONBlobSpider):
    name = "chesters_th"
    item_attributes = {"brand": "Chester's", "brand_wikidata": "Q5093401"}
    locations_key = ["data", "master_branchs", "data"]

    def start_requests(self):
        payload = json.dumps(
            {
                "query": """query {
    master_branchs(status: "active", brand_id: "62f9c84ebc4a20ae9e5ae88f") {
        data {
            address
            ref: branch_code
            latitude
            longitude
            phone: mobile
            region
            branch: title
            branch_time_detail {
                day
                status
                time_close
                time_open
            }
        }
    }
}"""
            }
        )
        url = "https://chester-api.chesters.co.th/api/gql"
        yield scrapy.Request(url=url, body=payload, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        for day_time in feature.get("branch_time_detail"):
            day = day_time.get("day")
            open_time = day_time.get("time_open")
            close_time = day_time.get("time_close")
            item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
        apply_category(Categories.FAST_FOOD, item)
        yield item
