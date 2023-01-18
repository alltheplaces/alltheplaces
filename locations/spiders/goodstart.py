import scrapy

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, DAYS_EN


class GoodstartSpider(scrapy.Spider):
    name = "goodstart"
    item_attributes = {
        "brand": "GoodStart Early Learning",
        "brand_wikidata": "Q24185325",
    }
    allowed_domains = ["goodstart.org.au"]
    start_urls = [
        "https://www.goodstart.org.au/find-centre/api/get-centres/-35.0004451/138.3309724/10000/",
    ]

    def parse(self, response):
        data = response.json()

        for i in data:
            item = DictParser.parse(i)
            item["website"] = "https://www.goodstart.org.au" + item.pop("website")
            item["image"] = "https://www.goodstart.org.au" + i["imageUrl"]
            item["addr_full"] = i["fullAddress"]
            item["street_address"] = i["address"]

            oh = OpeningHours()
            (hour_range, days_range) = i["hours"].split(", ")
            (from_time, close_time) = hour_range.split(" to ")
            (start_day, end_day) = days_range.split(" to ")
            for day in day_range(DAYS_EN[start_day], DAYS_EN[end_day]):
                oh.add_range(day, from_time, close_time, time_format="%I:%M%p")
            item["opening_hours"] = oh.as_opening_hours()

            apply_category(Categories.CHILD_CARE, item)
            yield item
