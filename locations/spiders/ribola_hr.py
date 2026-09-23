from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class RibolaHRSpider(JSONBlobSpider):
    name = "ribola_hr"
    item_attributes = {
        "brand": "Ribola",
        "brand_wikidata": "Q65124070",
    }
    start_urls = [
        "https://ribola.hr/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=50703d0778&load_all=1&layout=1"
    ]
    requires_proxy = "HR"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(feature["open_hours"])
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
