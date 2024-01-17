from json import loads

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DaisoUSSpider(Spider):
    name = "daiso_us"
    item_attributes = {"brand": "Daiso Japan", "brand_wikidata": "Q866991"}
    allowed_domains = ["daisous.com"]
    # Store finder is "Store Locator by Secomapp" (https://doc.storelocator.secomapp.com/)
    # Also appears to be rebadged as "ProMap Store Locator by AMAI" (https://help.amai.com/en/collections/3274749-promap-store-locator)
    start_urls = ["https://daisous.com/cdn/shop/t/68/assets/sca.storelocatordata.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response, **kwargs):
        for location in response.json():
            # Soon-to-open stores do not have the operating_hours field
            if not location.get("operating_hours"):
                continue

            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            hours_json = loads(location["operating_hours"])
            for day_abbrev, day_hours in hours_json.items():
                if day_hours["status"] != "1":
                    continue
                for slot in day_hours["slot"]:
                    item["opening_hours"].add_range(day_hours["name"], slot["from"], slot["to"])

            yield item
