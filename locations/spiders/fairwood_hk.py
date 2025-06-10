import json
from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FairwoodHKSpider(JSONBlobSpider):
    name = "fairwood_hk"
    item_attributes = {"brand": "大快活", "brand_wikidata": "Q5430935"}
    start_urls = ["https://www.fairwood.com.hk/stores"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = json.loads(response.xpath('//script[@type="application/json"]/text()').get())["props"]["pageProps"][
            "data"
        ]["stores"]
        return json_data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["city"] = feature["category"]
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            open_time = feature[day.lower() + "OpenHour"]
            close_time = feature[day.lower() + "CloseHour"]
            item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S")
        yield item
