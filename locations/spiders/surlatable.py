import re
from urllib.parse import parse_qs, urlsplit

import scrapy
from scrapy.linkextractors import LinkExtractor

from locations.hours import OpeningHours, day_range
from locations.linked_data_parser import LinkedDataParser


class SurLaTableSpider(scrapy.Spider):
    name = "surlatable"
    item_attributes = {"brand": "Sur La Table"}
    allowed_domains = ["surlatable.com"]
    start_urls = [
        "https://www.surlatable.com/stores",
    ]

    def parse(self, response):
        links = LinkExtractor(allow="/store-details").extract_links(response)
        yield from response.follow_all(links, callback=self.parse_store)

    def parse_store(self, response):
        ld = LinkedDataParser.find_linked_data(response, "Restaurant")
        item = LinkedDataParser.parse_ld(ld)

        oh = OpeningHours()
        for row in ld["openingHoursSpecification"].split("  ,"):
            if row in ["Holiday: Call store for holiday hours", "", "null"]:
                continue
            days, interval = row.split(": ")
            open_time, close_time = re.split(" *- *", interval)
            open_time = open_time.replace(" ", "")
            close_time = close_time.replace(" ", "")
            if open_time == "Noon":
                open_time = "12pm"
            if "-" in days:
                start_day, end_day = re.split(" *- *", days)
                for day in day_range(start_day[:2], end_day[:2]):
                    oh.add_range(day, open_time, close_time, "%I%p")
            else:
                oh.add_range(days[:2], open_time, close_time, "%I%p")
        item["opening_hours"] = oh.as_opening_hours()

        store_ld = LinkedDataParser.find_linked_data(response, "Store")
        item["name"] = store_ld["name"]
        item["website"] = response.url
        [item["ref"]] = parse_qs(urlsplit(response.url).query)["StoreID"]
        yield item
