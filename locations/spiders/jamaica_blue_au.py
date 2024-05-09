from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class JamaicaBlueAUSpider(Spider):
    name = "jamaica_blue_au"
    item_attributes = {"brand": "Jamaica Blue", "brand_wikidata": "Q24965819", "extras": Categories.CAFE.value}
    allowed_domains = ["jamaicablue.com.au"]
    start_urls = ["https://jamaicablue.com.au/wp-json/store-locator/v1/store/"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = location["address"]
            item["addr_full"] = clean_address([location.get("address"), location.get("address2")])
            item["website"] = location["web"]
            if location.get("opening_hours"):
                item["opening_hours"] = OpeningHours()
                hours_string = ""
                for day_hours in location["opening_hours"]:
                    hours_string = "{} {}: {}".format(hours_string, day_hours["days"], day_hours["hours"])
                item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
