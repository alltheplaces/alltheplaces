import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.lang_utils import katakana_to_hiragana
from locations.storefinders.canly import CanlySpider


class FreshnessBurgerJPSpider(CanlySpider):
    name = "freshness_burger_jp"
    item_attributes = {
        "brand_wikidata": "Q5503087",
    }
    brand_key = "630"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("businessStatus") == "CLOSED_PERMANENTLY":
            return

        # Some names carry an opening notice in brackets or a note after "※".
        branch = re.sub(r"^【[^】]*】", "", feature["nameKanji"]).split("※")[0]
        branch = re.sub(r"^(フレッシュネスバーガー|フレュシュネスバーガー|チーズネスバーガー)", "", branch)
        item["branch"] = branch.strip()
        if kana := feature.get("nameKana"):
            item["extras"]["branch:ja-Hira"] = katakana_to_hiragana(kana)
        item["website"] = f"https://search.freshnessburger.co.jp/detail/{feature['storeCode']}/"
        item["extras"]["start_date"] = feature.get("openingDate")

        yield item
