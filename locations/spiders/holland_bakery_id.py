from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature


class HollandBakeryIDSpider(Spider):
    name = "holland_bakery_id"
    item_attributes = {"branch": "Holland Bakery", "brand_wikidata": "Q19726345"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.hollandbakery.co.id/get-group", headers={"X-Requested-With": "XMLHttpRequest"}
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for city in response.json():
            for location in city["detail_toko"]:
                if not location:
                    continue
                item = Feature()
                item["ref"] = location["id"]
                item["branch"] = location["name"]
                item["lat"] = location["latitude"]
                item["lon"] = location["longitude"]
                item["phone"] = location["no_telp1"]
                item["street_address"] = location["alamat"]
                item["extras"]["check_date"] = location["updated"]

                yield item
