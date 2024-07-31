from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MarketplaceFreshAUSpider(Spider):
    name = "marketplace_fresh_au"
    item_attributes = {"brand": "MarketPlace Fresh", "brand_wikidata": "Q117847717"}
    allowed_domains = ["marketplacefresh.com.au"]
    start_urls = ["https://marketplacefresh.com.au/wp-json/mpfresh/v1/map"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["link"]
            item["housenumber"] = location["location"].get("street_number")
            item["street"] = location["location"]["street_name"]
            item["city"] = location["location"]["city"]
            item["postcode"] = location["location"]["post_code"]
            item["state"] = location["location"]["state_short"]
            item["addr_full"] = location["location"]["address"]
            item["phone"] = Selector(text=location["phone"]).xpath("//a/text").get()
            item["website"] = location["link"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                location["hours"].replace("<strong>", "").replace("</strong>", "")
            )
            yield item
