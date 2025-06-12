from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GoGrillBGSpider(JSONBlobSpider):
    name = "go_grill_bg"
    item_attributes = {"brand": "Go Grill", "brand_wikidata": "Q122839782"}
    start_urls = ["https://gogrill.bg/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature.get("store").replace("GO GRILL • ", "")
        item["website"] = None
        
        apply_category(Categories.RESTAURANT, item)
        
        yield item
