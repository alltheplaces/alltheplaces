from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class FreshnessBurgerJPSpider(Spider):
    name = "freshness_burger_jp"

    start_urls = ["https://g9ey9rioe.api.hp.can-ly.com/v2/companies/630/shops/search"]
    item_attributes = {
        "brand_wikidata": "Q5503087",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["shops"]:

            item = DictParser.parse(store)

            item["branch"] = (
                store.get("nameKanji").removeprefix("フレッシュネスバーガー").removeprefix("チーズネスバーガー")
            )
            item["extras"]["branch:ja-Hira"] = store.get("nameKana")
            item["website"] = f"https://search.freshnessburger.co.jp/detail/{store.get('storeCode')}/"
            item["extras"]["start_date"] = store.get("openingDate")
            item["ref"] = store.get("storeCode")

            yield item
