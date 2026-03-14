import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MaryBrownsCASpider(JSONBlobSpider):
    name = "mary_browns_ca"
    item_attributes = {"brand": "Mary Brown's", "brand_wikidata": "Q6779125"}
    start_urls = ["https://marybrowns.com/locations/"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        raw_data = response.xpath('//script[@id="scripts-js-extra"]/text()').get()
        data = json.loads(re.search(r"var _locations = (.*?);", raw_data).group(1))
        return data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        oh = OpeningHours()
        for key, value in feature.items():
            if key in [item.lower() for item in DAYS_FULL]:
                oh.add_ranges_from_string(key + " " + value)
        item["opening_hours"] = oh
        apply_category(Categories.FAST_FOOD, item)
        yield item
