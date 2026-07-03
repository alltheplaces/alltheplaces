from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BipaATSpider(JSONBlobSpider):
    name = "bipa_at"
    item_attributes = {"brand": "Bipa", "brand_wikidata": "Q864933"}
    start_urls = ["https://www.bipa.at/bff/stores"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["latitude"]:
            item["branch"] = item.pop("name").replace("BIPA Filiale ", "")
            opening_hours = OpeningHours()
            for day, range in feature["storeHours"].items():
                opening_hours.add_ranges_from_string(f"{day}: {range}")
                item["opening_hours"] = opening_hours
            apply_category(Categories.SHOP_CHEMIST, item)
            yield item
