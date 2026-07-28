from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LornaJaneAUNZSpider(JSONBlobSpider):
    name = "lorna_jane_au_nz"
    item_attributes = {"brand": "Lorna Jane", "brand_wikidata": "Q28857986"}
    start_urls = [
        "https://s3.ap-southeast-2.amazonaws.com/cdn.folkal.com/json_response/872cf56f-7317-11f0-8758-0aa8e15148ab.json",  # AU
        "https://s3.ap-southeast-2.amazonaws.com/cdn.folkal.com/json_response/3e70ca1c-98d0-11f0-ae0c-0aa8e15148ab.json",  # NZ
    ]
    locations_key = "locations"

    def pre_process_data(self, feature: dict) -> None:
        for key in ["address_1", "address_2", "street_name", "street_number", "website_url"]:
            feature.pop(key, None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["unique_id"]
        item["branch"] = item.pop("name").removeprefix("Lorna Jane").strip()
        item["opening_hours"] = OpeningHours()
        for rule in feature.get("timetable") or []:
            if rule["isClosed"]:
                item["opening_hours"].set_closed(rule["dayOfWeek"])
            else:
                item["opening_hours"].add_range(rule["dayOfWeek"], rule["openTime"], rule["closeTime"])
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
