from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class YeepGBSpider(WpGoMapsSpider):
    name = "yeep_gb"
    item_attributes = {"brand": "Yeep", "brand_wikidata": "Q123421114"}
    allowed_domains = ["yeeplockers.com"]
    map_id = 2

    def post_process_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        apply_category(Categories.PARCEL_LOCKER, item)
        item["branch"] = item.pop("name").removeprefix("YEEP! ")
        yield item
