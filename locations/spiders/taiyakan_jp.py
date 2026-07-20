from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TaiyakanJPSpider(Spider):
    name = "taiyakan_jp"
    item_attributes = {
        "brand": "タイヤ館",
        "brand_wikidata": "Q11315808",
    }
    start_urls = ["https://www.taiyakan.co.jp/api/v2/search"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for shop in data.get("shops", []):
            item = Feature()
            item["ref"] = str(shop["id"])
            item["name"] = shop["name"]
            item["branch"] = shop["name"].removeprefix("タイヤ館 ").removeprefix("タイヤ館")
            item["lat"] = shop["coords"]["lat"]
            item["lon"] = shop["coords"]["lng"]
            item["state"] = shop.get("pref")
            item["city"] = shop.get("city")
            item["addr_full"] = shop.get("address")
            item["phone"] = shop.get("tel")
            item["website"] = shop.get("url")
            apply_category(Categories.SHOP_CAR_PARTS, item)
            yield item

        if next_offset := data.get("next"):
            yield response.follow(f"/api/v2/search?offset={next_offset}", callback=self.parse)
