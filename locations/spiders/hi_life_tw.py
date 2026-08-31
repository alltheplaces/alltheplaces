from typing import Any

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

BASE = "https://www.hilife.com.tw/webapi/api"


class HiLifeTWSpider(Spider):
    name = "hi_life_tw"
    item_attributes = {"brand": "萊爾富", "brand_wikidata": "Q11326216"}

    async def start(self) -> Any:
        yield Request(url=f"{BASE}/AntiForgery/GetAntiForgeryToken", callback=self.parse_token)

    def parse_token(self, response: Response, **kwargs: Any) -> Any:
        token = response.json()["token"]
        yield JsonRequest(
            url=f"{BASE}/DistrictList/GetDistrictList",
            data={},
            headers={"X-XSRF-TOKEN": token},
            callback=self.parse_cities,
            cb_kwargs=dict(token=token),
        )

    def parse_cities(self, response: Response, token: str) -> Any:
        for city in response.json()["Entries"]:
            yield JsonRequest(
                url=f"{BASE}/ShopServices/GetShopServices",
                data={"City_Id": city["city_id"], "Town_Id": "", "Shop_Id": "", "Services": [], "Shop_Name": ""},
                headers={"X-XSRF-TOKEN": token},
                callback=self.parse_shops,
            )

    def parse_shops(self, response: Response, **kwargs: Any) -> Any:
        for shop in response.json()["Entries"]:
            item = Feature()
            item["ref"] = shop["shop_id"]
            item["branch"] = shop["shop_name"]
            item["addr_full"] = shop["shop_adr"]
            item["phone"] = shop["shop_tel"]
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
