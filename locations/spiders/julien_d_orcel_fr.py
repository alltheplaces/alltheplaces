import json
from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class JulienDOrcelFRSpider(JSONBlobSpider):
    name = "julien_d_orcel_fr"
    item_attributes = {"brand": "Julien d'Orcel", "brand_wikidata": "Q62497463"}
    start_urls = ["https://www.juliendorcel.com/bijouterie"]
    name_is_branch = True

    def extract_json(self, response: TextResponse) -> list[dict]:
        return chompjs.parse_js_object(response.text.split("var stores = ", 1)[1])

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id_externe"]
        item["branch"] = item["branch"].removeprefix("Julien d'Orcel - ")
        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])
        item["website"] = feature["url"].split("?", 1)[0]

        item["opening_hours"] = OpeningHours()
        for day, (hours,) in zip(DAYS, json.loads(feature["hours"])):
            if hours:
                # "09:30 - 12:30 - 14:00 - 19:00" when closed for lunch
                times = hours.split(" - ")
                for open_time, close_time in zip(times[::2], times[1::2], strict=True):
                    item["opening_hours"].add_range(day, open_time, close_time)
            else:
                item["opening_hours"].set_closed(day)
        yield item
