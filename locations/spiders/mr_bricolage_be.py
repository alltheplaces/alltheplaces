import json
import re
from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MrBricolageBESpider(JSONBlobSpider):
    name = "mr_bricolage_be"
    item_attributes = {"brand": "Mr. Bricolage", "brand_wikidata": "Q3141657"}
    start_urls = ["https://www.mr-bricolage.be/magasins"]

    def extract_json(self, response: Response) -> list:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var extendStore")]')
            .re_first(r"var extendStore[=\s]+({.+})\s*;")
            .replace("formated", "formatted")
        )["stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Mr.Bricolage ")
        item["website"] = feature.get("urlStore")
        item["facebook"] = feature.get("fb_url")
        item["opening_hours"] = OpeningHours()
        for index, rule in enumerate(json.loads(feature.get("hours", "[]"))):
            for shift in rule:
                if match := re.search(r"(\d\d:\d\d).+?(\d\d:\d\d)", shift):
                    item["opening_hours"].add_range(DAYS[index], *match.groups())
        yield item
