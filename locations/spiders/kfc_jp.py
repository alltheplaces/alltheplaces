from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser


class KfcJPSpider(Spider):
    name = "kfc_jp"
    item_attributes = {"brand_wikidata": "Q524757"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for points in ["x", "wv", "wy"]:
            yield JsonRequest(url=f"https://search.kfc.co.jp/api/points/{points}")

    def parse(self, response):
        for location in response.json()["items"]:
            location.update(location.pop("extra_fields"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location["key"]
            item["postcode"] = location["郵便番号"]
            item["city"] = location["市区町村"]
            item["website"] = "https://search.kfc.co.jp/points/" + item["ref"]
            apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("ドライブスルー"), False)
            apply_yes_no(Extras.DELIVERY, item, location.get("お届けケンタッキー") == "1", False)
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, location.get("クレジットカード"), False)
            apply_yes_no(PaymentMethods.PAYPAY, item, location.get("QRコード決済"), False)
            yield item
