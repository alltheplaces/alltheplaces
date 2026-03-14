import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SwensensTHSpider(JSONBlobSpider):
    name = "swensens_th"
    item_attributes = {"brand": "Swensen's", "brand_wikidata": "Q6640658"}
    start_urls = ["https://brandsite.swensens1112.com/js/575.72824bfd.js"]
    no_refs = True

    def extract_json(self, response: Response) -> dict | list[dict]:
        data = re.search(r"const va=JSON\.parse\('(.+?)'\)", response.text.replace("\\", "")).group(1)
        locations = json.loads(data)
        return locations

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"] = feature["Lattitude"]
        item["lon"] = feature["Longtitude"]
        item["branch"] = item["extras"]["branch:en"] = feature["StoreNameEN"]
        item["extras"]["branch:th"] = feature["StoreNameTH"]
        apply_category(Categories.ICE_CREAM, item)
        yield item
