import json
from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GohealthUrgentCareUSSpider(JSONBlobSpider):
    name = "gohealth_urgent_care_us"
    item_attributes = {"brand": "GoHealth Urgent Care", "brand_wikidata": "Q110282081"}
    start_urls = ["https://www.gohealthuc.com/locations"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        return json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]["centers"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").strip()
        item["postcode"] = str(item["postcode"])
        item["image"] = feature["image"]["url"].split("?")[0]
        item["website"] = f'https://www.gohealthuc.com/{feature["jv"]}/locations/{feature["uid"]}'
        item["extras"]["ref:google:place_id"] = feature.get("google_place_id")
        yield item
