from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class NewWorldNZSpider(Spider):
    name = "new_world_nz"
    item_attributes = {"brand": "New World", "brand_wikidata": "Q7012488"}
    allowed_domains = ["www.newworld.co.nz"]
    start_urls = ["https://www.newworld.co.nz/BrandsApi/BrandsStore/GetBrandStores"]
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["website"] = "https://www.newworld.co.nz" + location["url"]
            hours_string = location["openingHours"].replace("day-", "day: ")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
