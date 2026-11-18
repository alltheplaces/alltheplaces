from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class CocoIchibanyaSpider(GogaStoreLocatorSpider):
    name = "coco_ichibanya"
    skip_auto_cc_domain = True
    item_attributes = {"brand": "CoCo Ichibanya", "brand_wikidata": "Q5986105"}
    start_urls = ["https://worldwide.ichibanya.co.jp/api/point"]
    geohashes = ["g", "t", "q", "w", "x", "8", "9"]
    geohash_suffix = "/"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = source_feature["name"].replace("店", "")
        item["name"] = None
        try:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(
                DAYS,
                source_feature["営業時間(From)"].replace("：", ":"),
                source_feature["営業時間(To)"].replace("：", ":"),
            )
        except Exception:
            item["opening_hours"] = None

        apply_category(Categories.RESTAURANT, item)

        yield item
