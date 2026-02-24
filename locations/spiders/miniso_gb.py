import json
from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MinisoGBSpider(JSONBlobSpider):
    name = "miniso_gb"
    item_attributes = {"brand": "Miniso", "brand_wikidata": "Q20732498"}
    start_urls = ["https://minisoshop.co.uk/store-locator"]
    drop_attributes = {"facebook", "phone", "email", "twitter"}
    requires_proxy = "GB"

    def extract_json(self, response: Response) -> dict | list[dict]:
        data_raw = response.xpath("//script[contains(text(), 'jsonLocations:')]/text()").get()
        data_raw = data_raw.replace("pageData.push({ stores: ", "").replace("});", "")
        data_raw = data_raw.split('jsonLocations: {"items":', 1)[1]
        features_dict = chompjs.parse_js_object(data_raw)
        return features_dict

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("MINISO ", "").split(", ")[0]
        item["street_address"] = item.pop("addr_full")
        oh = OpeningHours()
        for day in DAYS_FULL:
            time = json.loads(feature["time_store"])[f"{day.lower()}"]
            if json.loads(feature["time_store"])[f"{day.lower()}_time"] == "1":
                if int(time["from"]["hours"]) == 0:
                    time["from"]["hours"] = "12"
                    open_time = time["from"]["hours"] + ":" + f'{time["to"]["minutes"]:02}' + "PM"
                else:
                    open_time = time["from"]["hours"] + ":" + f'{time["to"]["minutes"]:02}'
                    if int(time["from"]["hours"]) > 7:
                        open_time = open_time + "AM"
                    else:
                        open_time = open_time + "PM"
                if int(time["to"]["hours"]) == 0:
                    time["to"]["hours"] = "12"
                close_time = time["to"]["hours"] + ":" + f'{time["to"]["minutes"]:02}' + "PM"
                oh.add_range(day, open_time, close_time, "%I:%M%p")
        item["opening_hours"] = oh

        yield item
