import json
from urllib.parse import urljoin

from scrapy.http import Response, TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


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
        item["street_address"] = merge_address_lines(ld_data["addressLines"])
        item["phone"] = ld_data["phoneNumbers"][0]
        item["website"] = urljoin("https://locations.eatnpark.com/", ld_data["localPageUrl"])
        try:
            oh = OpeningHours()
            for day_time in ld_data["formattedBusinessHours"]:
                oh.add_ranges_from_string(day_time)
            item["opening_hours"] = oh
        except:
            pass
        yield item
