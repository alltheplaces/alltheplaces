from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class CanDOJPSpider(Spider):
    name = "can_do_jp"
    item_attributes = {
        "brand": "キャンドゥ",
        "brand_wikidata": "Q11297367",
    }
    start_urls = ["https://g9ey9rioe.api.hp.can-ly.com/v2/companies/1209/shops/search"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["shops"]:

            item = DictParser.parse(store)
            item["name"] = "キャンドゥ"
            item["ref"] = store["storeCode"]
            item["website"] = f"https://shopinfo.cando-web.co.jp/detail/{store['storeCode']}/"
            if store["phoneNumber"] is not None:
                item["phone"] = f"+81 {store['phoneNumber']}"
            item["branch"] = store["nameKanji"].removeprefix("Can★Doセレクト").removeprefix("Can★Do")
            item["extras"]["branch:ja-Hira"] = store["nameKana"]
            item["postcode"] = store["postalCode"]
            item["addr_full"] = store["address"]

            yield item
