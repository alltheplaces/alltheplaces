from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LeonidasSpider(JSONBlobSpider):
    name = "leonidas"
    item_attributes = {"brand": "Leonidas", "brand_wikidata": "Q80335"}
    start_urls = ["https://my-leonidas.com/api/public/store-locator"]
    locations_key = "shops"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["website"] = feature.get("official_page_urls").get("en")
        item["branch"] = item.pop("name").upper().removeprefix("LEONIDAS ")
        try:
            oh = OpeningHours()
            for day, value in feature.get("opening_hours", []).items():
                if value:
                    for open_close_time in value:
                        open_time = open_close_time["opens"]
                        close_time = open_close_time["closes"]
                        oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh
        except:
            pass
        yield item
