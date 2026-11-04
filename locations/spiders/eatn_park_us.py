import json

from scrapy.http import Response, TextResponse

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

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["street_address"] = ld_data["address_line_1"]
        item["phone"] = ld_data["formatted_phone"]
        try:
            oh = OpeningHours()
            for day_time in ld_data["formatted_business_hours"]:
                oh.add_ranges_from_string(day_time)
            item["opening_hours"] = oh
        except:
            pass
        yield item
