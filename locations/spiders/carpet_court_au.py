import html
import json

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CarpetCourtAUSpider(Spider):
    name = "carpet_court_au"
    item_attributes = {"brand": "Carpet Court", "brand_wikidata": "Q117156437"}
    allowed_domains = ["www.carpetcourt.com.au"]
    start_urls = ["https://www.carpetcourt.com.au/stores"]

    def parse(self, response):
        locations = json.loads((response.xpath('//div[@id="store-selector"]/following::script/text()').get().split("availableStores\": ", 1))[1].split("          }\n", 1)[0])
        for location_ref, location in locations.items():
            item = DictParser.parse(location)
            item["street_address"] = html.unescape(item.pop("addr_full")).strip(" ,")
            match location["state"]:
                case "513":
                    item["state"] = "Victoria"
                case "516":
                    item["state"] = "New South Wales"
                case "519":
                    item["state"] = "Queensland"
                case "522":
                    item["state"] = "Australian Capital Territory"
                case "525":
                    item["state"] = "South Australia"
                case "528":
                    item["state"] = "Western Australia"
                case "531":
                    item["state"] = "Northern Territory"
                case "534":
                    item["state"] = "Tasmania"
                case _:
                    item.pop("state")
            item["website"] = "https://www.carpetcourt.com.au/stores/" + html.unescape(location["url_key"])
            yield Request(url=item["website"], meta={"item": item}, callback=self.add_hours)

    def add_hours(self, response):
        item = response.meta["item"]
        if response.xpath('//div[contains(@class, "amlocator-location-image")]'):
            item["image"] = ((response.xpath('//div[contains(@class, "amlocator-location-image")]/@style').get().split("url('", 1))[1].split("');", 1))[0]
        item["opening_hours"] = OpeningHours()
        hours_string = " ".join(response.xpath('//div[contains(@class, "amlocator-schedule-table")]/div/span/text()').getall())
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
