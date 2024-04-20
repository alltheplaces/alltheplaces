from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonAUSpider(Spider):
    name = "decathlon_au"
    item_attributes = DecathlonFRSpider.item_attributes
    allowed_domains = ["decathlon.com.au"]
    start_urls = ["https://www.decathlon.com.au/api/store-setting?countryCode=AU"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["lat"] = location["address"].get("latitude")
            item["lon"] = location["address"].get("longitude")
            item["addr_full"] = clean_address([location["address"].get("street"), location["address"].get("city")])
            item["phone"] = location.get("phone1")
            item.pop("street", None)  # "street" is a full address sometimes
            item.pop("city", None)  # "city" field in source data mixes city and state
            item.pop("state", None)  # "city" field in source data mixes city and state

            item["opening_hours"] = OpeningHours()
            for day_hours in location["workingHours"]:
                item["opening_hours"].add_range(DAYS[day_hours["day"] - 1], day_hours["open"], day_hours["close"])

            yield item
