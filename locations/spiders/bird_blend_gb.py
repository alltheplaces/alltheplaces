from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BirdBlendGBSpider(JSONBlobSpider):
    name = "bird_blend_gb"
    item_attributes = {"brand": "Bird & Blend Tea Co", "brand_wikidata": "Q116985265"}
    start_urls = ["https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/8827/stores.js"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "Bird & Blend" in item["name"]:
            item["branch"] = item["name"].replace("Bird & Blend Tea Co. - ", "")
        apply_category(Categories.SHOP_TEA, item)
        yield item
