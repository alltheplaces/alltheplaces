from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import apply_category, Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BosCoffeePHQASpider(JSONBlobSpider):
    name = "bos_coffee_ph_qa"
    item_attributes = {"brand": "Bo's Coffee", "brand_wikidata": "Q30591352"}
    start_urls = ["https://storelocator.metizapps.com/v2/api/front/store-locator/?shop=bos-coffee.myshopify.com"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        if website := item.get("website"):
            if not website.startswith("http"):
                item["website"] = f"https://{website}"

        apply_category(Categories.CAFE, item)

        oh = OpeningHours()
        oh.add_ranges_from_string(feature.get("hour_of_operation"))
        item["opening_hours"] = oh

        yield item
