import re
from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FreshstopZASpider(JSONBlobSpider):
    name = "freshstop_za"
    item_attributes = {"brand": "FreshStop", "brand_wikidata": "Q116620734"}
    locations_key = "data"

    async def start(self) -> AsyncIterator[JsonRequest | Request]:

        yield JsonRequest(
            url="https://freshstop.co.za/wp-admin/admin-ajax.php",
            method="POST",
            headers={"content-type": "application/x-www-form-urlencoded"},
            body="action=list_stores&lat=28.6327&lng=77.2198",
            callback=self.parse,
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = feature["store_permalink"]
        item["lat"], item["lon"] = re.search(r".*=(-?\d+\.\d+),(-?\d+\.\d+)", feature["maps_url"]).groups()
        yield item
