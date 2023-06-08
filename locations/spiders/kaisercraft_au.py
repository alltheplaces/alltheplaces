import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KaisercraftAUSpider(Spider):
    name = "kaisercraft_au"
    item_attributes = {"brand": "Kaisercraft", "brand_wikidata": "Q118342651"}
    allowed_domains = ["cdn.shopify.com"]
    start_urls = ["https://cdn.shopify.com/s/files/1/1816/2071/t/543/assets/sca.storelocatordata.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if "OPENING SOON" in location["name"].upper():
                continue
            item = DictParser.parse(location)
            if location.get("description"):
                # Where the closing times fail to have a PM suffix,
                # add the PM suffix to avoid misinterpretation of
                # the closing time as AM.
                hours_string = re.sub(r"-\s*(\d{1,2}[.:][03]0)\s*(?!PM)", r"-\1PM", location.get("description").upper())
                hours_string = " ".join(hours_string.replace("<br>", " ").split())
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
