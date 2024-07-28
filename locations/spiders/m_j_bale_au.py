from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class MJBaleAUSpider(Spider):
    name = "m_j_bale_au"
    item_attributes = {"brand": "M.J. Bale", "brand_wikidata": "Q97516243"}
    allowed_domains = ["portal.mjbale.io"]
    start_urls = ["https://portal.mjbale.io/api/store/"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            if location["shopType"] != "Store":
                continue
            item = DictParser.parse(location)
            item["ref"] = location["number"]
            item["street_address"] = clean_address([location["address"]["address1"], location["address"]["address2"]])
            item.pop("website")
            item["email"] = location["website"]
            item["opening_hours"] = OpeningHours()
            for day_range in location["open_hours"]:
                start_time = day_range["time_start"]
                start_time = f"{start_time:04}"
                end_time = day_range["time_end"]
                end_time = f"{end_time:04}"
                if day_range["day_start"] > day_range["day_end"]:
                    for i in range(day_range["day_start"], 7):
                        item["opening_hours"].add_range(DAYS[i - 1], start_time, end_time, "%H%M")
                    for i in range(0, day_range["day_end"] + 1):
                        item["opening_hours"].add_range(DAYS[i - 1], start_time, end_time, "%H%M")
                else:
                    for i in range(day_range["day_start"], day_range["day_end"] + 1):
                        item["opening_hours"].add_range(DAYS[i - 1], start_time, end_time, "%H%M")
            yield item
