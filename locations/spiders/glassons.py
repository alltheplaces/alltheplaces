import re

import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GlassonsSpider(Spider):
    name = "glassons"
    item_attributes = {"brand": "Glassons", "brand_wikidata": "Q118384067"}
    allowed_domains = ["www.glassons.com"]
    start_urls = ["https://www.glassons.com/store-locations/all-stores-worldwide"]

    def parse(self, response):
        location_data = (
            response.xpath('//script[contains(text(), "var ga_stores = ")]/text()')
            .get()
            .split("var ga_stores = ", 1)[1]
            .split(" // all store data", 1)[0]
        )
        locations = chompjs.parse_js_object(location_data)
        for location_ref, location in locations.items():
            item = DictParser.parse(location)
            item["name"] = location["label"]
            item["street_address"] = re.sub(r"\s+", " ", item["addr_full"]).strip()
            item["website"] = (
                "https://www.glassons.com/store-locations/"
                + location["region"].lower()
                + "/"
                + location["label"].lower().replace(",", "").replace(" ", "-")
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                re.sub(r"\s+", " ", location["openinghours"].replace(",", " "))
            )
            yield item
