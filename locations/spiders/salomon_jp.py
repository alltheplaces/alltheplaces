from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SalomonJPSpider(Spider):
    name = "salomon_jp"

    start_urls = ["https://store.amersports.jp/api/points/xn7"]
    allowed_domains = ["store.amersports.jp"]
    country_code = "JP"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)
            item["ref"] = store["key"]
            item["website"] = f"https://store.amersports.jp/detail/{store['key']}"
            if "tel" in store["extra_fields"]:
                item["phone"] = f"+81 {store['extra_fields']['tel']}"
            if "郵便番号" in store["extra_fields"]:
                item["postcode"] = store["extra_fields"]["郵便番号"]
            if "直営店" in store["extra_fields"]["店舗種別"]:
                item["brand_wikidata"] = "Q2120822"
            if "スポーツスタイル" in store["extra_fields"]:
                apply_category(Categories.SHOP_CLOTHES, item)
            sport = []
            if "スキー" in store["extra_fields"]:
                sport.append("skiing")
            if "スノーボード" in store["extra_fields"]:
                sport.append("snowboard")
            if "アウトドア/ランニング" in store["extra_fields"]:
                sport.append("running")
            if sport:
                apply_category(Categories.SHOP_SPORTS, item)
                if len(sport) == 1:
                    item["extras"]["sport"] = sport[0]
                else:
                    item["extras"]["sport"] = ";".join(sport)

            yield item
