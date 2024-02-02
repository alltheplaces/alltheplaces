from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TheBrassTapUSSpider(Spider):
    name = "the_brass_tap_us"
    item_attributes = {"brand": "The Brass Tap", "brand_wikidata": "Q64358002"}
    allowed_domains = ["www.brasstapbeerbar.com"]
    start_urls = [
        "https://www.brasstapbeerbar.com/pinsNearestBrassTap.ashx?lat1=27.950&lon1=-82.45&range=100000&food=%25&lunch=%25&brunch=%25&music=%25"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if location.get("comingsoon") and location.get("comingsoon") == "X":
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            item["postcode"] = item.get("postcode").strip()
            item["website"] = "https://www.brasstapbeerbar.com/" + location.get("urltag")
            yield Request(url=item["website"], meta={"item": item}, callback=self.add_hours)

    def add_hours(self, response):
        item = response.meta["item"]
        hours_string = " ".join(filter(None, response.xpath('//div[@id="MainContent_divHours"]//text()').getall()))
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
