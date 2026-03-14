from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChatimeAUSpider(JSONBlobSpider):
    name = "chatime_au"
    item_attributes = {"brand": "Chatime", "brand_wikidata": "Q16829306"}
    allowed_domains = ["chatime.com.au"]
    start_urls = ["https://chatime.com.au/stores/?_data=routes%2Fstores._index"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["isComingSoon"]:
            return
        item["branch"] = item.pop("name").removeprefix("Chatime ")
        item["postcode"] = str(feature["postcode"])
        item["website"] = "https://chatime.com.au/stores/" + feature["slug"]
        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in feature["openingHours"].items():
            item["opening_hours"].add_range(day_name.title(), day_hours["openingTime"], day_hours["closingTime"])
        apply_category(Categories.CAFE, item)
        yield item
