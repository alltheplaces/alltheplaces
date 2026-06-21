from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BenesseBestudioJPSpider(Spider):
    name = "benesse_bestudio_jp"
    item_attributes = {"brand": "ベネッセビースタジオ", "brand_wikidata": "Q817123"}
    start_urls = ["https://school.benesse-bestudio.com/bbs/api/proxy2/shop/list"]

    def make_request(self, offset: int, limit: int = 500) -> JsonRequest:
        return JsonRequest(
            f"https://school.benesse-bestudio.com/bbs/api/proxy2/shop/list?limit={limit}&offset={offset}"
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for location in data["items"]:
            item = Feature()
            item["ref"] = location["code"]
            item["branch"] = location["name"]
            item["phone"] = location.get("phone")
            item["addr_full"] = location.get("address_name")
            item["postcode"] = location.get("postal_code")
            item["country"] = "JP"
            if coord := location.get("coord"):
                item["lat"] = coord.get("lat")
                item["lon"] = coord.get("lon")
            item["website"] = "https://school.benesse-bestudio.com/bbs/spot/detail?code={}".format(location["code"])
            apply_category(Categories.LANGUAGE_SCHOOL, item)
            yield item

        pager = data["count"]
        if pager["offset"] + pager["limit"] < pager["total"]:
            yield self.make_request(pager["offset"] + pager["limit"], pager["limit"])
