from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class CostaCoffeeUSSpider(Spider):
    name = "costacoffee_us"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["us.costacoffee.com"]
    start_urls = ["https://us.costacoffee.com/api/cf/?content_type=storeLocatorStore"]
    page_size = 1000

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=f"{url}&limit={self.page_size}")

    def parse(self, response):
        for location in response.json()["items"]:
            item = DictParser.parse(location["fields"])
            item["ref"] = location["sys"]["id"]
            item["addr_full"] = location["fields"]["storeAddress"]
            item["opening_hours"] = OpeningHours()
            for day_name in [s.lower() for s in DAYS_FULL]:
                open_time = location["fields"].get(f"{day_name}Opening")
                close_time = location["fields"].get(f"{day_name}Closing")
                if open_time and "24 HOURS" in open_time.upper():
                    item["opening_hours"].add_range(day_name, "00:00", "24:00")
                elif open_time and close_time:
                    item["opening_hours"].add_range(day_name, open_time, close_time)
            apply_category(Categories.COFFEE_SHOP, item)
            yield item

        offset = response.json()["skip"]
        if offset + response.json()["limit"] < response.json()["total"]:
            yield JsonRequest(url=f"{response.request.url}&limit={self.page_size}&offset={offset}")
