from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


class CocoIchibanyaJPSpider(Spider):
    name = "coco_ichibanya_jp"

    start_urls = ["https://tenpo.ichibanya.co.jp/api/point/xn/"]
    allowed_domains = ["tenpo.ichibanya.co.jp"]
    country_code = "JP"

    item_attributes = {
        "brand_wikidata": "Q5986105",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)
            item["ref"] = store["key"]
            item["website"] = f"https://tenpo.ichibanya.co.jp/map/{store['key']}"
            item["extras"]["addr:province"] = store["extra_fields"]["住所(都道府県)"]
            item["city"] = store["extra_fields"]["住所(市町村区郡)"]
            item["street_address"] = store["extra_fields"]["住所(その他)"]
            item["postcode"] = store["extra_fields"]["郵便番号"]
            item["branch"] = store["name"]
            item["extras"]["branch:jp"] = store["name"]
            item["extras"]["branch:en"] = store["extra_fields"]["店舗名（英語）"]
            try:
                item["phone"] = f"+81 {store['extra_fields']['TEL']}"
            except:
                pass
            item["extras"]["capacity"] = store["extra_fields"]["座席数"]
            if store["extra_fields"]["24時間営業"] == "1":
                item["opening_hours"] = "24/7"
            apply_yes_no(Extras.DRIVE_THROUGH, item, store["extra_fields"]["ドライブスルー"] == "1")
            apply_yes_no(Extras.DELIVERY, item, store["extra_fields"]["宅配"] == "1")
            if store["extra_fields"]["カウンターのみ（座席）"] == "1":
                item["extras"]["indoor_seating"] = "bar_table"
            if store["extra_fields"]["駐車場"] == "1":
                item["extras"]["parking"] = "yes"
            if store["extra_fields"]["お子様メニュー"] == "1":
                item["extras"]["child"] = "yes"
            if store["extra_fields"]["ベビーフード"] == "1":
                item["extras"]["baby"] = "yes"
            item["extras"]["website:orders"] = store["extra_fields"]["モバイルオーダー"]
            item["name"] = None

            yield item
