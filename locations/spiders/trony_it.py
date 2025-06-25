from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TronyITSpider(JSONBlobSpider):
    name = "trony_it"
    item_attributes = {"brand": "Trony", "brand_wikidata": "Q3999692"}
    start_urls = ["https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/23693-2wIRLy4IYixCQqpO/stores.js"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
