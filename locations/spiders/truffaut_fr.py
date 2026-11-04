import re
from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import TextResponse

from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TruffautFRSpider(JSONBlobSpider):
    name = "truffaut_fr"
    item_attributes = {"brand_wikidata": "Q3162640"}
    start_urls = ["https://www.truffaut.com/stores"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        data_raw = response.xpath('//script[contains(text(), "Smile_StoreLocator\\/retailer\\/search")]/text()').get()
        return parse_js_object(data_raw.split('"markers":', 1)[1])

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").strip()
        item["phone"] = location.get("contact_phone")

        # The address is one string: "street - more street - postcode CITY".
        street, _, town = location["address"].rpartition(" - ")
        if m := re.fullmatch(r"(\d{5}) (.+)", town):
            item.pop("addr_full", None)
            item["postcode"], item["city"] = m.groups()
            item["street_address"] = street.replace(" - ", ", ")

        # openingHours starts on Sunday; an empty day is closed.
        oh = OpeningHours()
        for day, ranges in zip(DAYS_FROM_SUNDAY, location["schedule"].get("openingHours") or []):
            if not ranges:
                oh.set_closed(day)
            for time_range in ranges:
                oh.add_range(day, time_range["start_time"], time_range["end_time"])
        item["opening_hours"] = oh

        yield item
