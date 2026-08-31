from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class TaitoSpider(Spider):
    name = "taito"
    item_attributes = {"brand_wikidata": "Q1054844"}

    start_urls = ["https://www.taito.co.jp/api/LanguageStoreSearch/?isGlobalOnly=false&lang=ja"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            store.update(store.pop("StoreData"))
            item = DictParser.parse(store)
            item["ref"] = store.get("StoreID")
            if "http" in store.get("LinkUrl"):
                item["website"] = store.get("LinkUrl")
            else:
                item["website"] = f"https://www.taito.co.jp{store.get('LinkUrl')}"
            item["image"] = "https://" + store.get("ImagePath") + store.get("MobileImageName01")
            item["extras"]["branch:ja-Hira"] = store.get("StoreNameCana")
            item["phone"] = store.get("TelephoneNo")
            yield item
