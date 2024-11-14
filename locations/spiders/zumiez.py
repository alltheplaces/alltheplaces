import html
import re
from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ZumiezSpider(JSONBlobSpider):
    name = "zumiez"
    item_attributes = {"brand": "Zumiez", "brand_wikidata": "Q8075252"}
    start_urls = ["https://www.zumiez.com/graphql?hash=505530338"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        return response.json()["data"]["getStores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("has_store_page"):
            item["website"] = f"https://www.zumiez.com/stores/{feature.get('identifier')}"
        try:
            s = html.unescape(feature.get("store_hours"))
            oh = OpeningHours()
            for day in re.findall('content="([\w\s:-]+)"', s):
                splits = day.replace("-", " ").split(" ")
                oh.add_range(splits[0], splits[1], splits[2])
            item["opening_hours"] = oh
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours: {e}")
        yield item
