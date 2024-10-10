import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class BulgarianPostsBGSpider(Spider):
    name = "bulgarian_posts_bg"
    item_attributes = {"operator": "Български пощи", "operator_wikidata": "Q2880826"}
    allowed_domains = ["bgpost.bg"]
    start_urls = ["https://bgpost.bg/api/offices?search_by_city_name_or_address="]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url)

    def parse(self, response):
        for location in response.json():
            location["street_address"] = location.pop("address", None)
            item = DictParser.parse(location)
            item["name"] = location["office_name"]
            item["city"] = location["city_name"]
            item["state"] = location["district"]
            item["phone"] = location["phone"]
            item["opening_hours"] = OpeningHours()

            has_break = False
            if location["note"] is not None:
                if break_times := re.match(r"(\d+:\d+)-(\d+:\d+) - затворено", location["note"]):
                    break_start = break_times.group(1)
                    break_end = break_times.group(2)
                    has_break = True

            for day_name in DAYS_FULL:
                if location[f"working_hours_{day_name.lower()}"]:
                    try:
                        day_hours = location[f"working_hours_{day_name.lower()}"].split("-", 1)
                        if has_break:
                            item["opening_hours"].add_range(day_name, day_hours[0], break_start, "%H:%M")
                            item["opening_hours"].add_range(day_name, break_end, day_hours[1], "%H:%M")
                        else:
                            item["opening_hours"].add_range(day_name, *day_hours, "%H:%M")
                    except ValueError:
                        continue
            apply_category(Categories.POST_OFFICE, item)
            yield item
