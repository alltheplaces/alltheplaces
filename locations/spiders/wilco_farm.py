import re

import chompjs

from locations.hours import OpeningHours, day_range
from locations.json_blob_spider import JSONBlobSpider


class WilcoFarmSpider(JSONBlobSpider):
    name = "wilco_farm"
    item_attributes = {"brand": "Wilco Farm", "brand_wikidata": "Q8000290"}
    allowed_domains = ["www.farmstore.com"]
    start_urls = ["https://www.farmstore.com/locations/"]
    requires_proxy = True

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "var markers")]/text()').get())

    def pre_process_data(self, location):
        for k in list(location.keys()):
            location[k.replace("store", "")] = location.pop(k)
        location["street_address"] = location.pop("Street")

    def post_process_item(self, item, response, location):
        item["opening_hours"] = OpeningHours()
        for start_day, end_day, start_time, end_time in re.findall(
            r"(\w+)(?: - (\w+))? (\d[ap]m)\s*-\s*(\d[ap]m)", location["Hours"]
        ):
            if not end_day:
                end_day = start_day
            item["opening_hours"].add_days_range(
                day_range(start_day, end_day), start_time, end_time, time_format="%I%p"
            )

        yield item
