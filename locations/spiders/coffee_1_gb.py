import re

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range
from locations.pipelines.address_clean_up import clean_address


class Coffee1GBSpider(scrapy.Spider):
    name = "coffee_1_gb"
    item_attributes = {"brand": "Coffee#1", "brand_wikidata": "Q22032058"}
    allowed_domains = ["www.coffee1.co.uk"]
    start_urls = ["https://www.coffee1.co.uk/locations/get"]

    def parse(self, response):
        for item in response.json():
            if " - closed" in item["post_title"].lower():
                continue
            yield scrapy.Request(item["url"], callback=self.parse_branch, meta={"item": item})

    def parse_branch(self, response):
        location = response.meta["item"]
        item = DictParser.parse(location)

        if "<br />" in location["branch_address"]:
            item["addr_full"] = clean_address(
                [i.strip(" ,") for i in location["branch_address"].split("<br />\r\n") if i]
            )
        else:
            item["addr_full"] = location["branch_address"]

        if "branch-fallback" not in location["branch_image"]:
            item["image"] = location["branch_image"]

        item["ref"] = re.search(r"/locations/([^/]+)/$", location["url"]).group(1)
        item["name"] = location["post_title"]
        item["city"] = location["branch_city"]
        phone = response.xpath(".//div[@class='locationmap-phone']//text()[2]").get()
        if phone:
            item["phone"] = phone.strip()

        extras = {
            "baby": Extras.BABY_CHANGING_TABLE,
            "bench": Extras.OUTDOOR_SEATING,
            "disabled": Extras.TOILETS_WHEELCHAIR,
            "dog": "dog",
            "wifi": Extras.WIFI,
        }

        for i in location["facilities"]:
            apply_yes_no(extras[i["post_name"]], item, True)

        apply_category(Categories.COFFEE_SHOP, item)
        item["opening_hours"] = OpeningHours()

        for row in response.css(".timetable-row"):
            day = row.css(".timetable-day::text").get().replace(" ", "")
            time = row.css(".timetable-time::text").get().replace(" ", "").upper()
            open_time, _, close_time = time.partition("-")
            time_format = "%I:%M%p" if "AM" in open_time else "%H:%M"
            if "-" not in day:
                item["opening_hours"].add_range(day, open_time, close_time, time_format=time_format)
                continue
            start, _, end = day.partition("-")
            days = day_range(start, end)
            item["opening_hours"].add_days_range(days, open_time, close_time, time_format=time_format)

        yield item
