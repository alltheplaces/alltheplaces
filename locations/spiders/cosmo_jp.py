from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
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

            item["name"] = "コスモ"
            item["branch"] = store.get("name").removesuffix("ＳＳ")
            item["extras"]["branch:ja-Hira"] = store.get("店名カナ")
            item["website"] = store.get("確認用URL")
            item["ref"] = store.get("key")
            apply_yes_no("full_service", item, store.get("フル"))
            apply_yes_no("self_service", item, store.get("セルフ"))
            apply_yes_no("service:vehicle:inspection", item, store.get("車検"))
            apply_yes_no(Extras.CAR_WASH, item, store.get("洗車"))
            apply_yes_no(Fuel.ELECTRIC, item, store.get("EV急速充電器"))
            apply_yes_no("sells:food", item, store.get("セブン-イレブン複合店"))

            apply_yes_no(PaymentMethods.ID, item, store.get("Id"))
            apply_yes_no(PaymentMethods.WAON, item, store.get("WAON"))
            apply_yes_no(PaymentMethods.PAYPAY, item, store.get("PayPay"))
            apply_yes_no(PaymentMethods.QUICPAY, item, store.get("QUICPay"))
            apply_yes_no(PaymentMethods.D_BARAI, item, store.get("d払い"))
            apply_yes_no(PaymentMethods.RAKUTEN_PAY, item, store.get("楽天ペイ"))

            if store.get("24時間営業"):
                item["opening_hours"] = "24/7"

            apply_category(Categories.FUEL_STATION, item)

            yield item
