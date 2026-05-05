from typing import AsyncIterator

from scrapy import Request

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class HmvCASpider(JSONBlobSpider):
    name = "hmv_ca"
    item_attributes = {"brand": "HMV", "brand_wikidata": "Q10854572"}
    locations_key = "stores"

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in country_iseadgg_centroids("CA", 94):
            yield Request(
                f"https://www.hmv.ca/en/stores-findstores?lat={lat}&lng={lon}&loadMore=true&page=1&radius=100&results=50&showMap=false"
            )

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines([location.get("address1"), location.get("address2")])
        item["website"] = (
            f"https://www.hmv.ca/en/stores/{location['storePageUrl']}" if location.get("storePageUrl") else None
        )

        if hours_html := location.get("storeHours"):
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_html)
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_MUSIC, item)
        yield item
