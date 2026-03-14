import json
from typing import AsyncIterator

from scrapy.http import Request

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.pipelines.state_clean_up import STATES


class ElementsMassageCAUSSpider(JSONBlobSpider):
    name = "elements_massage_ca_us"
    item_attributes = {
        "brand": "Elements Massage",
        "brand_wikidata": "Q113642393",
    }
    locations_key = "locations"

    async def start(self) -> AsyncIterator[Request]:
        for country, states in STATES.items():
            for state in states:
                yield Request(f"https://elementsmassage.com/locator?q={state}%2C%20{country}&lat=0&lng=0")

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        item["website"] = response.urljoin(feature["slug"])

        item["street_address"] = merge_address_lines([feature["address"], feature["address_2"]])
        del item["addr_full"]

        if feature["fax_number"]:
            item["extras"]["fax"] = feature["fax_number"]

        item["facebook"] = feature["facebook_profile"]
        if item["facebook"] and not item["facebook"].startswith("http"):
            item["facebook"] = "https://" + item["facebook"]

        if feature["open_date"] and feature["open_date"] != "0000-00-00":
            item["extras"]["start_date"] = feature["open_date"]
        elif feature["projected_open_date"] and feature["projected_open_date"] != "0000-00-00":
            item["extras"]["start_date"] = feature["projected_open_date"]
        if feature["close_date"] and feature["close_date"] != "0000-00-00":
            item["extras"]["end_date"] = feature["close_date"]

        oh = OpeningHours()
        for day, hours in json.loads(feature["business_hours"]).items():
            if hours["closed"]:
                oh.set_closed(day)
            else:
                oh.add_range(day, hours["start"], hours["end"], time_format="%H:%M:%S")
        item["opening_hours"] = oh

        yield item
