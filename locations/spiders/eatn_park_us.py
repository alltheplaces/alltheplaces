import json
from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EatnParkUSSpider(JSONBlobSpider):
    name = "eatn_park_us"
    item_attributes = {"brand": "Eat'n Park", "brand_wikidata": "Q5331211"}
    start_urls = ["https://locations.eatnpark.com/"]

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        json_data = json.loads(response.xpath('//*[@type="application/json"]/text()').get())["props"]["pageProps"][
            "locations"
        ]
        return json_data

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = feature["address_line_1"]
        item["phone"] = feature["formatted_phone"]
        try:
            oh = OpeningHours()
            for day_time in feature["formatted_business_hours"]:
                oh.add_ranges_from_string(day_time)
            item["opening_hours"] = oh
        except:
            pass
        yield item
