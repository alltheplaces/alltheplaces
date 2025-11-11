from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChestersTHSpider(JSONBlobSpider):
    name = "chesters_th"
    item_attributes = {"brand": "Chester's", "brand_wikidata": "Q5093401"}
    locations_key = ["data", "master_branchs", "data"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://chester-api.chesters.co.th/api/gql",
            data={
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
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["branch"]
        item["opening_hours"] = OpeningHours()
        for day_time in feature.get("branch_time_detail"):
            item["opening_hours"].add_range(day_time["day"], day_time["time_open"], day_time["time_close"])
        apply_category(Categories.FAST_FOOD, item)
        yield item
