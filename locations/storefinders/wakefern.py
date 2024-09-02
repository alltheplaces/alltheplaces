import json
import re

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class WakefernSpider(JSONBlobSpider):
    """
    Unknown software shared by most Wakefern (https://www2.wakefern.com/) sub-
    brands, as well as Smart & Final, and possibly others.

    To use, specify the homepage in start_urls.
    """

    def extract_json(self, response):
        script = response.xpath("//script[contains(text(), '__PRELOADED_STATE__')]/text()").get()
        script = script[script.index("{") :]
        return json.loads(script)["stores"]["availablePlanningStores"]["items"]

    def pre_process_data(self, location):
        location["street_address"] = merge_address_lines(
            [location["addressLine1"], location["addressLine2"], location["addressLine3"]]
        )
        location["state"] = location["countyProvinceState"]

    def post_process_item(self, item, response, location):
        item["ref"] = location["retailerStoreId"]
        item["website"] = f"{self.start_urls[0]}sm/planning/rsid/{item['ref']}"

        if "name" in item:
            split_name = re.split(r"\s+of\s+", item["name"], flags=re.IGNORECASE)
            if len(split_name) == 2:
                item["name"], item["branch"] = split_name

        if "openingHours" in location and location["openingHours"] is not None:
            oh = OpeningHours()
            oh.add_ranges_from_string(location["openingHours"])
            item["opening_hours"] = oh

        yield item
