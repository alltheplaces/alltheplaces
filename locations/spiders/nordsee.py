from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NordseeSpider(JSONBlobSpider):
    name = "nordsee"
    item_attributes = {"brand": "Nordsee", "brand_wikidata": "Q74866"}
    start_urls = ["https://www.nordsee.com/de/filialen"]

    def extract_json(self, response: Response) -> list:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(),"latitude")]/text()').get(), unicode_escape=True
        )["stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item.get("state") in ["AT", "DE"]:
            item["country"] = item.pop("state")
        item["website"] = response.url
        item["phone"] = item["phone"].replace("\\/", "") if item.get("phone") else None
        if hours := feature.get("orari"):
            item["opening_hours"] = OpeningHours()
            for rule in hours.get("ristorante", {}).values():
                if day := sanitise_day(rule.get("label"), DAYS_DE):
                    for shift in [
                        ("lunch_start", "lunch_end"),
                        ("dinner_start", "dinner_end"),
                    ]:
                        open_time = rule.get(shift[0])
                        close_time = rule.get(shift[1]) or rule.get("dinner_end")
                        item["opening_hours"].add_range(day, open_time, close_time)

        yield item
