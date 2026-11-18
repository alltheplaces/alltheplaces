import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class SogoPharmacyJPSpider(CanlySpider):
    name = "sogo_pharmacy_jp"
    item_attributes = {"operator": "総合メディカル", "operator_wikidata": "Q11607556"}
    brand_key = "1058"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # Most pharmacies are named "<brand> <branch>店". The group runs そうごう薬局
        # and several acquired chains (みよの台薬局, ハロー薬局, ...). Single
        # pharmacies have no branch part and keep their own name.
        name = feature["nameKanji"].strip()
        if m := re.fullmatch(r"(\S+)[ 　]+(.+)", name):
            item["brand"] = m.group(1)
            item["branch"] = m.group(2).removesuffix("店")
            item["name"] = m.group(1)
        else:
            item["name"] = name

        item["website"] = f"https://shop.sogo-pharmacy.jp/detail/{feature['storeCode']}/"

        apply_category(Categories.PHARMACY, item)
        apply_yes_no(Extras.DISPENSING, item, True)

        yield item
