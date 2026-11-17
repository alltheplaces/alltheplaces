from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsMYSpider(JSONBlobSpider):
    name = "mcdonalds_my"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = [
        "https://www.mcdonalds.com.my/locate-us/stores?distance=100000&lat=&lng=&state=&category=&address=&is_suggestion=0&is_locate=0"
    ]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item["ref"] = item.pop("name").removeprefix("McDonlad's ")
        apply_category(Categories.FAST_FOOD, item)
        yield item
