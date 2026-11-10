from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BuilditSpider(JSONBlobSpider):
    name = "buildit"
    item_attributes = {"brand": "Build it", "brand_wikidata": "Q116755810"}
    start_urls = ["https://buildit.co.za/api/stores"]
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address", {}))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = f'https://buildit.co.za/stores/{feature["id"]}'
        item["street_address"] = item.pop("street", "").replace("C\\O", "C/O")
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
