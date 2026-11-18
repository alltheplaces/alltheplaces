from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EdibleArrangementsUSSpider(JSONBlobSpider):
    name = "edible_arrangements_us"
    item_attributes = {"brand": "Edible Arrangements", "brand_wikidata": "Q5337996"}
    start_urls = ["https://api26.storepoint.co/v2/169fcf28194dc8/locations"]
    locations_key = ["results", "locations"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Edible® ").removeprefix("Edible Arrangements ")
        item["addr_full"] = item.pop("street_address")
        item["website"] = f'https://www.ediblearrangements.com/pages/find-a-store?selected={item["ref"]}'
        try:
            oh = OpeningHours()
            for day in DAYS_FULL:
                open_close_time = feature.get(day.lower())
                if open_close_time:
                    open_time, close_time = open_close_time.split("-")
                    oh.add_range(
                        day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
                    )
            item["opening_hours"] = oh
        except:
            pass
        yield item
