from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class CosmoJPSpider(Spider):
    name = "cosmo_jp"

    start_urls = ["https://map.cosmo-energy.co.jp/api/points"]
    item_attributes = {
        "brand_wikidata": "Q2498318",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:
            store.update(store.pop("extra_fields"))
            item = DictParser.parse(store)

            item["name"] = None
            item["branch"] = store.get("name").removesuffix("ＳＳ")
            item["extras"]["branch:ja-Hira"] = store.get("店名カナ")
            item["operator"] = store.get("運営者名")
            item["website"] = store.get("確認用URL")
            item["ref"] = store.get("key")
            apply_yes_no("full_service", item, store.get("フル") == "1")
            apply_yes_no("self_service", item, store.get("セルフ") == "1")

            apply_category(Categories.FUEL_STATION, item)

            yield item
