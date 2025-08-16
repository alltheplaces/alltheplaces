from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class DogsTrustGBSpider(JSONBlobSpider):
    name = "dogs_trust_gb"
    item_attributes = {
        "brand_wikidata": "Q5288441",
        "brand": "Dogs Trust",
    }
    start_urls = ["https://www.dogstrust.org.uk/page-data/support-us/our-shops/charity-shops/page-data.json"]
    locations_key = ["result", "data", "allNodeCharityShop", "nodes"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update({k.replace("field_", ""): v for k, v in feature.items()})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.dogstrust.org.uk" + feature["path"]["alias"]
        item.pop("email", None)
        item.pop("facebook", None)
        item.pop("twitter", None)
        item["street_address"] = merge_address_lines([feature["address_line_one"], feature["address_line_two"]])
        if feature["opening_times_text"]:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(ranges_string=feature["opening_times_text"])
        apply_category(Categories.SHOP_CHARITY, item)
        yield item
