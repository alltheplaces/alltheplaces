from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class QdStoresGBSpider(JSONBlobSpider):
    name = "qd_stores_gb"
    item_attributes = {"name": "QD Stores", "brand": "QD Stores", "brand_wikidata": "Q22101973"}
    start_urls = [
        "https://storelocator.metizapps.com/v2/api/front/store-locator/?shop=bde5e8-2.myshopify.com&_t=1775759065863"
    ]
    locations_key = "stores"
    drop_attributes = {"email"}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([item.pop("addr_full"), feature["address2"]])
        item["branch"] = item.pop("name").removeprefix("QD ")
        slug = item["branch"].replace(" ", "-").lower()
        item["website"] = "https://www.qdstores.co.uk/pages/" + slug + "-qd"
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        oh = OpeningHours()
        oh.add_ranges_from_string(feature["hour_of_operation"])
        item["opening_hours"] = oh
        yield item
