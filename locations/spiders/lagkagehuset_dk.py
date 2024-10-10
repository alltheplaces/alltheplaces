import re
from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider


class LagkagehusetDKSpider(JSONBlobSpider):
    name = "lagkagehuset_dk"
    item_attributes = {"brand": "Lagkagehuset", "brand_wikidata": "Q12323572"}
    start_urls = ["https://lagkagehuset.dk/select-shop"]

    def extract_json(self, response: Response) -> list:
        return chompjs.parse_js_object(
            re.search(r"\\\"shops\\\":(\[.+?\])}", response.text).group(1), unicode_escape=True
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name")
        item["email"] = feature.get("mail")
        if all(feature.get("openingHours", {}).get(day.lower()) == "0:00-0:00" for day in DAYS_3_LETTERS):
            set_closed(item)
        else:
            item["opening_hours"] = OpeningHours()
            for day, hours in feature.get("openingHours").items():
                item["opening_hours"].add_range(day, *hours.split("-"))
        yield item
