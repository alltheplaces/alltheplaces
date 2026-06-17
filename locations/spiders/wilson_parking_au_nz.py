from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WilsonParkingAUNZSpider(JSONBlobSpider):
    name = "wilson_parking_au_nz"
    item_attributes = {"brand": "Wilson Parking", "brand_wikidata": "Q28448427"}
    locations_key = "carParks"

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        for domain in ["wilsonparking.co.nz", "www.wilsonparking.com.au"]:
            yield JsonRequest(
                url=f"https://{domain}/api/v2/GetParkingByLocation?latitude=0&longitude=0&sort=undefined&distance=200000000"
            )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["website"] = item["ref"] = response.urljoin(item["website"])
        item["addr_full"] = feature["location"]["address"]
        yield item
