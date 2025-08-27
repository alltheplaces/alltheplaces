from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class SevenandifsJPSpider(Spider):
    name = "sevenandifs_jp"

    start_urls = ["https://shop.7andi-fs.co.jp/api/point/xn/"]
    allowed_domains = ["shop.7andi-fs.co.jp"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            match store["marker"]["ja"]["name"]:
                case "デニーズ":
                    item.update({"brand_wikidata": "Q11320661"})
                    apply_category(Categories.RESTAURANT, item)
                case _:
                    apply_category(Categories.RESTAURANT, item)

            if store["extra_fields"]["24時間営業"] == "1":
                item["opening_hours"] = "24/7"
            item["website"] = f"https://shop.7andi-fs.co.jp/map/{store['key']}/"
            item["phone"] = f"+81 {store['extra_fields']['電話番号']}"
            apply_yes_no("parking", item, store["extra_fields"]["駐車場あり"] == "1")
            apply_yes_no("toilets:wheelchair", item, store["extra_fields"]["だれでもトイレ"] == "1")
            apply_yes_no("changing_table", item, store["extra_fields"]["ベビーシート"] == "1")
            apply_yes_no("delivery", item, store["extra_fields"]["出前サービス"] == "1")
            apply_yes_no("elevator", item, store["extra_fields"]["エレベーター"] == "1")
            apply_yes_no("wheelchair", item, store["extra_fields"]["車椅子対応の入り口"] == "1")
            if store["extra_fields"]["コンセント"] == "1":
                item["extras"]["socket:nema_5_15"] = "yes"
            if store["extra_fields"]["全席禁煙"] == "1":
                item["extras"]["smoking"] = "no"
            item["postcode"] = store["extra_fields"]["郵便番号"]

            yield item
