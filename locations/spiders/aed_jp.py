from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AedJPSpider(Spider):
    name = "aed_jp"
    country_code = "JP"

    async def start(self) -> AsyncIterator[Request]:
        yield self.get_page(1)

    def get_page(self, n):
        return Request(
            f"https://www.qqzaidanmap.jp/api/aed/list?limit=100&page={n}",
            meta={"page": n},
        )

    def parse(self, response):
        data = response.json()
        aeds = data["aeds"]

        for aed in aeds:
            item = DictParser.parse(aed)
            item["ref"] = aed["id"]
            item["website"] = (
                f"https://www.qqzaidanmap.jp/map/my_map?latitude={aed["location"]["latitude"]}&longitude={aed["location"]["longitude"]}&zoom=16&id={aed["id"]}"
            )
            item["lat"] = aed["location"]["latitude"]
            item["lon"] = aed["location"]["longitude"]
            apply_category(Categories.DEFIBRILLATOR, item)
            item["extras"]["defibrillator:location"] = aed["install_address_detail"]
            item["street_address"] = aed["install_address"]
            item["extras"]["addr:province"] = aed["install_prefecture_name"]
            item["name"] = aed["install_location_name"]

            yield item

        if data["pages"]["current_page"] < 2:  # data["pages"]["current_page"] < data["pages"]["total_pages"]:
            yield self.get_page(1 + response.meta["page"])
