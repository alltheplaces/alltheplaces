from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.lang_utils import katakana_to_hiragana
from locations.storefinders.canly import CanlySpider


class CanDOJPSpider(CanlySpider):
    name = "can_do_jp"
    item_attributes = {
        "brand": "キャンドゥ",
        "brand_wikidata": "Q11297367",
    }
    brand_key = "1209"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("businessStatus") == "CLOSED_PERMANENTLY":
            return

        item["name"] = "キャンドゥ"
        item["branch"] = feature["nameKanji"].removeprefix("Can★Doセレクト").removeprefix("Can★Do").strip()
        if kana := feature.get("nameKana"):
            item["extras"]["branch:ja-Hira"] = katakana_to_hiragana(kana)
        item["website"] = f"https://shopinfo.cando-web.co.jp/detail/{feature['storeCode']}/"
        if phone := feature.get("phoneNumber"):
            item["phone"] = f"+81 {phone}"

        yield item
