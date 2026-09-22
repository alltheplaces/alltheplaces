from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.hours import OpeningHours, DAYS_FULL
from locations.pipelines.address_clean_up import merge_address_lines


class TjhughesGBSpider(JSONBlobSpider):
    name = "tjhughes_gb"
    item_attributes = {"name": "TJ Hughes", "brand": "TJ Hughes", "brand_wikidata": "Q7672651"}

    start_urls = [
        "https://www.tjhughes.co.uk/apps/store-locator/stores/surrounding?shop=tj-hughes-store.myshopify.com&latitude=52.624192&longitude=-1.423577&max_distance=0&limit=0&calc_distance=0&record_search=0&usage_surface=proxy_map&distance_unit=MI&store_name_like=",
    ]
    locations_key = ["stores"]


    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([item.pop("addr_full"), feature.get("address2")])
        item["postcode"] = feature["postal_zip"]
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
