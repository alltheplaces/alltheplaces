from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class SnappySnapsGBSpider(JSONBlobSpider):
    name = "snappy_snaps_gb"
    item_attributes = {"brand": "Snappy Snaps", "brand_wikidata": "Q7547351"}
    allowed_domains = ["www.snappysnaps.co.uk"]
    start_urls = ["https://www.snappysnaps.co.uk/storefinder/locator/get/_featured_/_/"]
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines([feature.get("street1"), feature.get("street2")])
        item["website"] = feature["website"] + "/more-times"
        item["email"] = feature["misc5"]

        item["opening_hours"] = OpeningHours()
        for day_index, day_abbrev in enumerate(DAYS):
            day_hours = feature["opening_{}".format(day_index + 1)].replace(" ", "")
            if day_hours == "Closed":
                item["opening_hours"].set_closed(day_abbrev)
                continue
            item["opening_hours"].add_range(day_abbrev, *day_hours.split("-", 1))

        apply_category(Categories.SHOP_PHOTO, item)

        yield item
