from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_HR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NtlHRSpider(JSONBlobSpider):
    name = "ntl_hr"
    item_attributes = {"brand": "NTL", "brand_wikidata": "Q6966095"}
    start_urls = ["https://ntl.hr/prodajna-mjesta"]

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(),"var locations")]/text()').re_first(
                r"var locations[=\s]+(\[.+\];)"
            )
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = self.item_attributes["brand"]
        item["branch"] = feature["place"].split(" ")[-1]
        item["street_address"] = item.pop("street")
        item["opening_hours"] = self.parse_opening_hours(feature.get("working_hours", []))
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            if day := sanitise_day(rule.get("name"), DAYS_HR):
                if rule.get("time") == "Zatvoreno":
                    oh.set_closed(day)
                else:
                    open_time, close_time = rule["time"].split("-")
                    oh.add_range(day, open_time.strip(), close_time.strip())
        return oh
