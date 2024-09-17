import json
import re

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class VeggieGrillUSSpider(Spider):
    name = "veggie_grill_us"
    item_attributes = {"brand": "Veggie Grill", "brand_wikidata": "Q18636427"}
    start_urls = ["https://www.veggiegrill.com/locations/"]

    def parse(self, response):
        script = response.xpath("//script[contains(text(), 'locations:')]/text()").get()
        i = script.find("locations:")
        locations = json.loads(script[i : script.find("\n", i) - 1].removeprefix("locations:"))
        for location in locations:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin(location["url"])
            item["image"] = location["fields"]["herobasic"]["images"][0]["image_url"]
            item["extras"]["ref:google"] = location["google_place_id"]
            item["street_address"] = item.pop("street")

            oh = OpeningHours()
            oh.add_ranges_from_string(re.sub("<[^<]+?>", "", location["hours"]))
            item["opening_hours"] = oh

            yield item
