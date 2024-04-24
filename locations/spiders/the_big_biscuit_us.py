from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TheBigBiscuitUSSpider(Spider):
    name = "the_big_biscuit_us"
    item_attributes = {
        "brand": "The Big Biscuit",
        "brand_wikidata": "Q124125449",
        "extras": {"amenity": "restaurant", "cuisine": "american"},
    }
    allowed_domains = ["www.bigbiscuit.com"]
    start_urls = ["https://bigbiscuit.com/locations/"]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "var mapLocations = ")]/text()').get()
        js_blob = "[" + js_blob.split("var mapLocations = [", 1)[1].split("}];", 1)[0] + "}]"
        for location in parse_js_object(js_blob):
            if "COMING SOON" in location["name"].upper():
                continue
            item = DictParser.parse(location)
            item["ref"] = location["permalink"]
            # Opening hours are the same for all stores per FAQ at:
            # https://bigbiscuit.com/contact-the-big-biscuit/
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, "06:30", "14:30")
            yield item
