from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonAUSpider(Spider):
    name = "decathlon_au"
    item_attributes = DecathlonFRSpider.item_attributes
    allowed_domains = ["decathlon.com.au"]
    # Store finder is "Store Locator by Secomapp" (https://doc.storelocator.secomapp.com/)
    # Also appears to be rebadged as "ProMap Store Locator by AMAI" (https://help.amai.com/en/collections/3274749-promap-store-locator)
    start_urls = ["https://decathlon.com.au/cdn/shop/t/817/assets/sca.storelocatordata.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if "Decathlon Partner" in location["name"]:
                continue
            item = DictParser.parse(location)
            item["addr_full"] = ", ".join(filter(None, [location.get("address"), location.get("address2")]))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["schedule"])
            yield item
