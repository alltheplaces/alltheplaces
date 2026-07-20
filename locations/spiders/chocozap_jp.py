from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.items import Feature


class ChocozapJPSpider(Spider):
    name = "chocozap_jp"
    item_attributes = {
        "brand": "chocoZAP",
        "brand_wikidata": "Q117936896",
    }

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(1)

    def make_request(self, page: int) -> Request:
        return Request(
            f"https://chocozap.g.kuroco.app/rcms-api/34/studios?pageID={page}",
            meta={"page": page},
        )

    def parse(self, response):
        data = response.json()
        for location in data["list"]:
            item = Feature()
            item["ref"] = location["hacomono_studio_id"]
            item["branch"] = location["name"]
            item["addr_full"] = location["address"]
            item["lat"] = location["coords"]["gmap_y"]
            item["lon"] = location["coords"]["gmap_x"]
            item["website"] = f"https://chocozap.jp/studios/{location['hacomono_studio_id']}"
            apply_category(Categories.GYM, item)
            yield item

        page_info = data.get("pageInfo", {})
        current_page = page_info.get("pageNo", 1)
        total_pages = page_info.get("totalPageCnt", 1)
        if current_page < total_pages:
            yield self.make_request(current_page + 1)
