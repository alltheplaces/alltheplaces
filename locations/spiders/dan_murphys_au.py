from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class DanMurphysAUSpider(JSONBlobSpider):
    name = "dan_murphys_au"
    item_attributes = {"brand": "Dan Murphy's", "brand_wikidata": "Q5214075"}
    allowed_domains = ["api.danmurphys.com.au"]
    start_urls = ["https://api.danmurphys.com.au/apis/ui/StoreLocator/Stores/danmurphys"]
    locations_key = "Stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Invalid robots.txt cannot be parsed
    requires_proxy = "AU"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("AddressLine1"), feature.get("AddressLine2")])
        item["website"] = "https://www.danmurphys.com.au/stores/{}-{}-{}".format(
            feature["State"], feature["Name"].replace(" ", "-"), feature["Id"]
        )
        item["opening_hours"] = OpeningHours()
        hours_string = " ".join(
            [
                "{}: {}".format(day_hours["Day"], day_hours["Hours"])
                for day_hours in feature.get("OpeningHours", [])[:-1]
            ]
        )
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.SHOP_ALCOHOL, item)
        yield item
