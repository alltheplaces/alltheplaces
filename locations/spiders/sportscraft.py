from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class SportscraftSpider(Spider):
    name = "sportscraft"
    item_attributes = {"brand": "Sportscraft", "brand_wikidata": "Q7579966"}
    allowed_domains = ["www.sportscraft.com.au"]
    start_urls = ["https://www.sportscraft.com.au/custom_api/commercetools/channels"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["key"]
            item["name"] = item["name"].split("(", 1)[0].strip()
            item["street_address"] = clean_address([location["address1"].strip(), location["address2"].strip()])
            item["city"] = item["city"].strip()
            item["website"] = "https://www.sportscraft.com.au/store-locator/store-details?id=" + location["key"]
            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                if f"hours_{day}_open" in location.keys() and f"hours_{day}_close" in location.keys():
                    hours_string = (
                        f"{hours_string} {day}: " + location[f"hours_{day}_open"] + "-" + location[f"hours_{day}_close"]
                    )
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
