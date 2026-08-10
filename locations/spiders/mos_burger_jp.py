from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class MosBurgerJPSpider(Spider):
    name = "mos_burger_jp"
    item_attributes = {
        "brand": "モスバーガー",
        "brand_wikidata": "Q1204169",
    }
    start_urls = ["https://www.mos.jp/data/shop/shop.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["shops"]:

            item = DictParser.parse(store)
            item["name"] = "モスバーガー"
            item["ref"] = store["shop_cd"]
            item["website"] = f"https://www.mos.jp/shop/detail/?shop_cd={store['shop_cd']}"
            item["phone"] = f"+81 {store['tel1']}-{store['tel2']}-{store['tel3']}"
            item["branch"] = store["name"].removeprefix("モスバーガー")
            item["extras"]["branch:ja-Hira"] = store["kana"].removeprefix("もすばーがー")
            item["postcode"] = f"{store['zip1']}-{store['zip2']}"
            item["extras"]["addr:province"] = store["pref_name"]
            item["addr_full"] = store["addr_all"]
            item["extras"]["start_date"] = store["openingday"]

            yield item
