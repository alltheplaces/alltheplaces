import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.area_marker import AreaMarkerSpider


class SmbcJPSpider(AreaMarkerSpider):
    name = "smbc_jp"
    item_attributes = {
        "brand": "三井住友銀行",
        "brand_wikidata": "Q2660418",
        "name": "三井住友銀行",
    }
    corp_id = "smbc-demo"
    referer = "https://www.areamarker.com/smbc-demo/top"
    fields = {
        "ref": "kyo_id",
        "name": "name",
        "lat": "lat_en",
        "lon": "lon_en",
        "addr": "addr_1",
        "phone": "tel_1",
        "col_1": "col_1",
        "col_2": "col_2",
        "col_3": "col_3",
        "col_4": "col_4",
        "col_7": "col_7",
        "col_10": "col_10",
        "col_16": "col_16",
    }

    def post_process_item(
        self, item: Feature, response: TextResponse, store: dict, raw_record: dict, **kwargs
    ) -> Iterable[Feature]:
        item["name"] = None
        branch = store["name"]
        branch = re.sub(r"\s*【[^】]*】\s*$", "", branch)
        branch = re.sub(r"\s*[（(][^）)]*[）)]\s*$", "", branch)
        item["branch"] = branch.strip()
        item["website"] = f"https://www.areamarker.com/smbc-demo/info/{store['ref']}"

        if store["col_1"] == "1" or store["col_7"] == "1" or store["col_10"] == "1" or store["col_4"] == "1":
            apply_category(Categories.BANK, item)
        elif store["col_2"] == "1" or store["col_3"] == "1":
            apply_category(Categories.ATM, item)
        elif store["col_16"] == "1":
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)

        yield item
