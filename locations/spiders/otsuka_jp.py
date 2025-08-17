from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class OtsukaJPSpider(Spider):
    name = "otsuka_jp"

    start_urls = ["https://shop-eql.otsuka.co.jp/api/poi"]
    allowed_domains = ["shop-eql.otsuka.co.jp"]
    country_code = "JP"
    SKIP_BRANDS = [
        "マツモトキヨシ",
        "ぱぱす",
        "ファミリードラッグ",
        "くすりのラブ",
        "ココカラファイン",
        "セガミ",
        "ジップ",
        "ライフォート",
        "コダマ",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            if any(i in store["name"] for i in self.SKIP_BRANDS):
                item = {}
                yield item
            item = DictParser.parse(store)
            item["ref"] = store["key"]
            item["website"] = f"https://shop-eql.otsuka.co.jp/map/{store['key']}"
            if store["marker_index"] == 1:
                apply_category(Categories.PHARMACY, item)
                item["extras"]["dispensing"] = "yes"
            else:
                apply_category(Categories.CLINIC, item)

            yield item
