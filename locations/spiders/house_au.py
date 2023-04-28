from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class HouseAUSpider(Spider):
    name = "house_au"
    item_attributes = {"brand": "House", "brand_wikidata": "Q117921987"}
    allowed_domains = ["www.house.com.au"]
    start_urls = ["https://www.house.com.au/service/storeLocator/findNearestStore"]
    custom_settings = {
        "COOKIES_ENABLED": True,
    }

    def start_requests(self):
        yield Request(url="https://www.house.com.au/", callback=self.start_requests_with_cookie)

    def start_requests_with_cookie(self, response):
        for url in self.start_urls:
            yield JsonRequest(url=url, data={}, method="POST")

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["WarehouseCode"]
            if "House Bed and Bath" in item["name"]:
                item["brand"] = "House Bed & Bath"
            item["street_address"] = ", ".join(filter(None, [location.get("AddressLine1"), location.get("AddressLine2")]))
            item["website"] = "https://www.house.com.au/store-locator/" + item["name"].lower().replace(" ", "-")
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                open_time = location[f"{day_name}Open"].strip().replace(".", ":")
                close_time = location[f"{day_name}Close"].strip().replace(".", ":")
                item["opening_hours"].add_range(day_name, open_time, close_time)
            yield item
