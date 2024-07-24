from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BatteryWorldAUSpider(Spider):
    name = "battery_world_au"
    item_attributes = {"brand": "Battery World", "brand_wikidata": "Q124003678"}
    allowed_domains = ["www.batteryworld.com.au"]
    start_urls = ["https://www.batteryworld.com.au/app/services/Store.Service.ss"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location.get("internalid")
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            item["website"] = "https://www.batteryworld.com.au/stores/" + location.get("urlcomponent")
            hours_html = Selector(text=location.get("openingHours"))
            hours_string = " ".join(hours_html.xpath(".//text()").getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
