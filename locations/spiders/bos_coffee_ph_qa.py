from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BosCoffeePHQASpider(JSONBlobSpider):
    name = "bos_coffee_ph_qa"
    item_attributes = {
        "brand_wikidata": "Q30591352",
        "brand": "Bo's Coffee",
    }
    start_urls = ["https://storelocator.metizapps.com/v2/api/front/store-locator/?shop=bos-coffee.myshopify.com"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        if website := item.get("website"):
            if "https" not in website:
                item["website"] = f"https://{website}" if "http" not in website else website
        else:
            item["website"] = "https://www.boscoffee.com/"
        oh = OpeningHours()
        oh.add_ranges_from_string(feature.get("hour_of_operation"))
        item["opening_hours"] = oh

        yield item
