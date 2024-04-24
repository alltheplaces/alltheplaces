from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours


class GallAndGallSpider(Spider):
    name = "gall_and_gall"
    item_attributes = {"brand": "Gall & Gall", "brand_wikidata": "Q13639185"}
    allowed_domains = ["www.gall.nl"]
    start_urls = [
        "https://www.gall.nl/on/demandware.store/Sites-gall-nl-Site/nl_NL/Stores-GetAll",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["website"] = "https://www.gall.nl/" + item["website"]
            item["housenumber"] = location["houseNr"] + location["houseNrAdditional"]

            item["opening_hours"] = OpeningHours()

            for day in location["storeHoursJSON"]:
                item["opening_hours"].add_ranges_from_string(day["day"] + " " + day["time"], days=DAYS_NL)

            yield item
