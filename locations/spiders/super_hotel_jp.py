from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class SuperHotelJPSpider(Spider):
    name = "super_hotel_jp"
    item_attributes = {"brand_wikidata": "Q11313858"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, offset: int, count: int = 100) -> JsonRequest:
        return JsonRequest(
            "https://pkg.navitime.co.jp/superhotel-map/api/proxy2/shop/list?offset={}&limit={}".format(offset, count)
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["items"]:
            item = Feature()
            item["ref"] = location["code"]
            item["branch"] = location["name"].replace("スーパーホテル", "")
            item["phone"] = location.get("phone")
            item["street_address"] = location["address_name"]
            # address_code?
            item["postcode"] = location["postal_code"]
            item["lon"] = location["coord"]["lon"]
            item["lat"] = location["coord"]["lat"]
            item["website"] = item["extras"]["website:ja"] = location["external_url"]
            slug = location["external_url"].split("/")[-2]
            item["extras"]["website:en"] = "https://www.superhoteljapan.com/en/s-hotels/{}/".format(slug)
            item["extras"]["website:kr"] = "https://www.superhoteljapan.com/kr/s-hotels/{}/".format(slug)
            item["extras"]["website:cn"] = "https://www.superhoteljapan.com/cn/s-hotels/{}/".format(slug)

            apply_category(Categories.HOTEL, item)

            yield item

        pager = response.json()["count"]
        if pager["offset"] + pager["limit"] < pager["total"]:
            yield self.make_request(pager["offset"] + pager["limit"], pager["limit"])
