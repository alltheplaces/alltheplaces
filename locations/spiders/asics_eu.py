from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AsicsEUSpider(JSONBlobSpider):
    name = "asics_eu"
    item_attributes = {"brand": "ASICS", "brand_wikidata": "Q327247"}
    allowed_domains = ["cdn.crobox.io"]
    start_urls = ["https://cdn.crobox.io/content/ujf067/stores.json"]
    skip_auto_cc_spider_name = True
    no_refs = True

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["storetype"] not in ["factory-outlet", "retail-store"]:
            return
        if store_name := item.pop("name", None):
            item["branch"] = store_name.removeprefix("ASICS Factory Outlet ").removeprefix("ASICS ")
        item["street_address"] = item.pop("addr_full")
        apply_category(Categories.SHOP_SHOES, item)
        if google_place_id := feature.get("google_place_id"):
            item["extras"]["ref:google:place_id"] = google_place_id
        yield item
