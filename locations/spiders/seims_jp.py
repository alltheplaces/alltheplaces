from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SeimsJPSpider(Spider):
    name = "seims_jp"
    start_urls = ["https://store.seims.co.jp/api/point/xn/"]
    allowed_domains = ["store.seims.co.jp"]
    item_attributes = {
        "brand_wikidata": "Q11456137",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            item["brand"] = store["marker"]["ja"]["name"]

            item["postcode"] = store["extra_fields"]["郵便番号"]
            item["extras"]["addr:province"] = store["extra_fields"]["都道府県"]
            item["extras"]["branch:ja-Hira"] = store["extra_fields"]["店名かな"]

            if store["extra_fields"]["電話番号"] is not None:
                item["phone"] = f"+81 {store['extra_fields']['電話番号']}"
                if store["extra_fields"]["調剤電話番号"] is not None:
                    item["extras"]["phone:pharmacy"] = f"+81 {store['extra_fields']['調剤電話番号']}"
            else:
                item["phone"] = f"+81 {store['extra_fields']['調剤電話番号']}"

            item["website"] = f"https://store.seims.co.jp/map/{store['key']}/"
            item["ref"] = store["key"]
            if store["extra_fields"]["ドラッグストア"] == "1":
                apply_category(Categories.SHOP_CHEMIST, item)
            if store["extra_fields"]["処方せん受付店舗"] == "1":
                apply_category(Categories.PHARMACY, item)
                item["extras"]["dispensing"] = "yes"

            yield item
