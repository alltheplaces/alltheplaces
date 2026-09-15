from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class CocoIchibanyaJPSpider(Spider):
    name = "coco_ichibanya_jp"
    item_attributes = {
        "brand_wikidata": "Q5986105",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for points in ["w", "xj", "xn", "xp", "z"]:
            yield JsonRequest(url=f"https://tenpo.ichibanya.co.jp/api/point/{points}/")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:
            extra_fields = store["extra_fields"]

            item = DictParser.parse(store)
            item["ref"] = store["key"]
            item["website"] = f"https://tenpo.ichibanya.co.jp/map/{store['key']}/"
            item["extras"]["addr:province"] = extra_fields.get("住所(都道府県)")
            item["city"] = extra_fields.get("住所(市町村区郡)")
            item["street_address"] = extra_fields.get("住所(その他)")
            item["postcode"] = extra_fields.get("郵便番号")
            item["branch"] = store["name"]
            item["extras"]["branch:jp"] = store["name"]
            item["extras"]["branch:en"] = extra_fields.get("店舗名（英語）")
            if (phone := extra_fields.get("TEL", "-")) != "-":
                item["phone"] = f"+81 {phone}"
            if (capacity := extra_fields.get("座席数", "0")) != "0":
                item["extras"]["capacity"] = capacity
            if extra_fields.get("24時間営業") == "1":
                item["opening_hours"] = "24/7"
            apply_yes_no(Extras.DRIVE_THROUGH, item, extra_fields.get("ドライブスルー") == "1")
            apply_yes_no(Extras.DELIVERY, item, extra_fields.get("宅配") == "1")
            if extra_fields.get("カウンターのみ（座席）") == "1":
                item["extras"]["indoor_seating"] = "bar_table"
            if extra_fields.get("駐車場") == "1":
                item["extras"]["parking"] = "yes"
            if extra_fields.get("お子様メニュー") == "1":
                item["extras"]["child"] = "yes"
            if extra_fields.get("ベビーフード") == "1":
                item["extras"]["baby"] = "yes"
            if (order_url := extra_fields.get("モバイルオーダー", "")).startswith("http"):
                item["extras"]["website:orders"] = order_url
            item["name"] = None

            apply_category(Categories.RESTAURANT, item)

            yield item
