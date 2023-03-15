from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CarpetCourtNZSpider(Spider):
    name = "carpet_court_nz"
    item_attributes = {"brand": "Carpet Court", "brand_wikidata": "Q117156437"}
    allowed_domains = ["carpetcourt.co.nz"]
    start_urls = ["https://carpetcourt.nz/wp-admin/admin-ajax.php?action=store_search&lat=0&lng=0&categories=&stories=0&max_results=100000&search_radius=500000"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = location["store"]
            item["street_address"] = item.pop("addr_full")
            if location["address2"]:
                item["street_address"] = item["street_address"] + ", " + location["address2"]
            if location["hours"]:
                item["opening_hours"] = OpeningHours()
                hours_string = " ".join(Selector(text=location["hours"]).xpath('//text()').getall())
                item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
